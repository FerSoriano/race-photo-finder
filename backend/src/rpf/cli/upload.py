"""`rpf upload` -- push photos + detections to the API.

Office step: back on the internet, this reads the manifest and uploads through
the admin API. The server owns the database and object storage; this CLI never
holds production credentials for either.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import httpx
import typer

from rpf.config import get_settings
from rpf.detection.manifest import Manifest

app = typer.Typer(help="Upload detected photos to the API.")


@app.command()
def upload(
    event: Annotated[str, typer.Option("--event", "-e", help="Event slug")],
    manifest_path: Annotated[Path, typer.Option("--manifest", "-m", help="Manifest file")],
    photos_dir: Annotated[
        Path | None,
        typer.Option("--photos", help="Photo folder (default: the manifest's folder)"),
    ] = None,
    api_url: Annotated[str | None, typer.Option("--api-url", help="API base URL")] = None,
    admin_key: Annotated[str | None, typer.Option("--admin-key", help="X-Admin-Key")] = None,
    create_event: Annotated[
        bool, typer.Option("--create-event", help="Create the event if it does not exist")
    ] = False,
    event_name: Annotated[
        str | None, typer.Option("--name", help="Event name, used with --create-event")
    ] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show what would upload")] = False,
) -> None:
    settings = get_settings()
    api_url = (api_url or settings.api_base_url).rstrip("/")
    admin_key = admin_key or settings.admin_api_key

    if not manifest_path.is_file():
        typer.secho(f"Manifest not found: {manifest_path}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    manifest = Manifest.load(manifest_path)
    if manifest.event_slug != event:
        typer.secho(
            f"Manifest is for event {manifest.event_slug!r}, not {event!r}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    photos_dir = photos_dir or manifest_path.parent
    headers = {"X-Admin-Key": admin_key}

    with httpx.Client(base_url=api_url, headers=headers, timeout=120.0) as client:
        if create_event:
            response = client.post(
                "/v1/admin/events",
                json={"slug": event, "name": event_name or event, "is_published": False},
            )
            if response.status_code == 409:
                typer.echo(f"Event {event!r} already exists")
            elif response.is_error:
                typer.secho(
                    f"Could not create event: {response.status_code} {response.text}",
                    fg=typer.colors.RED,
                    err=True,
                )
                raise typer.Exit(1)
            else:
                typer.secho(f"Created event {event!r}", fg=typer.colors.GREEN)

        # Ask the server what it already has, so we never send those bytes.
        response = client.get(f"/v1/admin/events/{event}/photos/hashes")
        if response.is_error:
            typer.secho(
                f"Could not reach the API: {response.status_code} {response.text}",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(1)
        already_uploaded = set(response.json())

        entries = [e for e in manifest.photos if e.error is None]
        pending = [e for e in entries if e.sha256 not in already_uploaded]

        typer.echo(
            f"{len(entries)} photos in manifest | {len(entries) - len(pending)} already on "
            f"the server | {len(pending)} to upload"
        )
        if dry_run:
            for entry in pending:
                typer.echo(f"  would upload {entry.filename} ({len(entry.bibs)} bibs)")
            return

        uploaded = skipped = failed = 0
        for i, entry in enumerate(pending, 1):
            path = photos_dir / entry.filename
            prefix = f"[{i}/{len(pending)}] {entry.filename}"
            if not path.is_file():
                typer.secho(f"{prefix}: file missing at {path}", fg=typer.colors.RED)
                failed += 1
                continue

            bibs_payload = json.dumps([asdict(b) for b in entry.bibs])
            with path.open("rb") as fh:
                response = client.post(
                    f"/v1/admin/events/{event}/photos",
                    files={"file": (entry.filename, fh, "image/jpeg")},
                    data={
                        "sha256": entry.sha256,
                        "bibs": bibs_payload,
                        "model_name": manifest.model,
                    },
                )

            if response.is_error:
                typer.secho(
                    f"{prefix}: {response.status_code} {response.text}", fg=typer.colors.RED
                )
                failed += 1
                continue

            if response.json()["created"]:
                uploaded += 1
                typer.echo(f"{prefix}: uploaded")
            else:
                skipped += 1
                typer.echo(f"{prefix}: already present")

    typer.secho(
        f"\nDone. {uploaded} uploaded, {skipped} already present, {failed} failed",
        fg=typer.colors.GREEN if not failed else typer.colors.YELLOW,
    )
    if failed:
        raise typer.Exit(1)
