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

from typing import TYPE_CHECKING, BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from rpf.storage.base import Visibility

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client


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

    def url(self, key: str, visibility: Visibility = "private") -> str:
        if visibility == "public" and self._public_base_url:
            return f"{self._public_base_url}/{key}"
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket_for(visibility), "Key": key},
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
