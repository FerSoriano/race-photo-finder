"""Generic S3-compatible storage.

Nothing here is provider-specific: Cloudflare R2, Backblaze B2, MinIO and AWS S3
are all reached by pointing `endpoint_url` / credentials at them from .env.

Two R2 quirks are accounted for and are harmless elsewhere:
  * the region must be the literal string "auto";
  * R2 does not implement GetBucketLocation, so bucket-region redirection has
    to stay off (`s3={"addressing_style": "path"}` + a fixed region avoids the
    lookup entirely).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, BinaryIO
from urllib.parse import quote

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from rpf.storage.base import Visibility

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client

# Anything that could break out of the quoted-string form of a header value, or
# smuggle a second header past it. Filenames reach us from an upload, so they
# are untrusted input on their way into a response header.
_UNSAFE_IN_FILENAME = re.compile(r'[\\"\r\n\x00-\x1f\x7f/]')


def content_disposition(filename: str) -> str:
    """Build an `attachment` disposition that survives an odd filename.

    The plain `filename=` form is ASCII-only, so a name with accents also gets
    the RFC 5987 `filename*` form -- browsers prefer it and fall back to the
    other one.
    """
    cleaned = _UNSAFE_IN_FILENAME.sub("_", filename).strip() or "download"
    ascii_name = cleaned.encode("ascii", "replace").decode("ascii")
    disposition = f'attachment; filename="{ascii_name}"'
    if ascii_name != cleaned:
        disposition += f"; filename*=UTF-8''{quote(cleaned, safe='')}"
    return disposition


class S3Storage:
    def __init__(
        self,
        bucket: str,
        *,
        public_bucket: str | None = None,
        endpoint_url: str | None = None,
        region: str = "auto",
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        public_base_url: str | None = None,
        presign_expires_seconds: int = 3600,
    ) -> None:
        self._bucket = bucket
        # Defaults to the private bucket so a misconfiguration fails closed:
        # objects stay unreachable rather than becoming world-readable.
        self._public_bucket = public_bucket or bucket
        self._public_base_url = public_base_url.rstrip("/") if public_base_url else None
        self._presign_expires = presign_expires_seconds
        self._client: S3Client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )

    def _bucket_for(self, visibility: Visibility) -> str:
        return self._public_bucket if visibility == "public" else self._bucket

    def put(
        self,
        key: str,
        data: BinaryIO,
        content_type: str = "image/jpeg",
        visibility: Visibility = "private",
    ) -> None:
        extra: dict[str, str] = {"ContentType": content_type}
        if visibility == "public":
            # Long cache: derivative keys are addressed by photo id and are
            # never rewritten in place.
            extra["CacheControl"] = "public, max-age=31536000, immutable"
        self._client.put_object(Bucket=self._bucket_for(visibility), Key=key, Body=data, **extra)

    def get(self, key: str, visibility: Visibility = "private") -> bytes:
        try:
            response = self._client.get_object(Bucket=self._bucket_for(visibility), Key=key)
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("NoSuchKey", "404"):
                raise FileNotFoundError(key) from exc
            raise
        return response["Body"].read()

    def url(
        self,
        key: str,
        visibility: Visibility = "private",
        download_filename: str | None = None,
    ) -> str:
        if visibility == "public" and self._public_base_url:
            # A CDN URL is a plain object URL; there is no request to sign, so
            # the disposition override cannot be attached to it.
            return f"{self._public_base_url}/{key}"
        params: dict[str, str] = {"Bucket": self._bucket_for(visibility), "Key": key}
        if download_filename:
            # Signed into the URL, so it cannot be tampered with in transit.
            params["ResponseContentDisposition"] = content_disposition(download_filename)
        return self._client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=self._presign_expires,
        )

    def exists(self, key: str, visibility: Visibility = "private") -> bool:
        try:
            self._client.head_object(Bucket=self._bucket_for(visibility), Key=key)
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("NoSuchKey", "NotFound", "404"):
                return False
            raise
        return True

    def delete(self, key: str, visibility: Visibility = "private") -> None:
        self._client.delete_object(Bucket=self._bucket_for(visibility), Key=key)
