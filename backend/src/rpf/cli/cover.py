"""`rpf cover` -- set or remove an event's cover image.

Office step, optional: a banner shown on the event card in place of the
frontend's slug-derived gradient placeholder. `--undo` clears it.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Annotated

import httpx
import typer

from rpf.config import get_settings

app = typer.Typer(help="Set or remove an event's cover image.")


@app.command()
def cover(
    event: Annotated[str, typer.Argument(help="Event slug")],
    file: Annotated[Path | None, typer.Argument(help="Cover image file (jpg/png/webp)")] = None,
    undo: Annotated[
        bool, typer.Option("--undo", help="Delete the cover instead of uploading")
    ] = False,
    api_url: Annotated[str | None, typer.Option("--api-url", help="API base URL")] = None,
    admin_key: Annotated[str | None, typer.Option("--admin-key", help="X-Admin-Key")] = None,
) -> None:
    if undo and file is not None:
        typer.secho("Pass either a file or --undo, not both", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    if not undo and file is None:
        typer.secho(
            "Missing file path (or pass --undo to delete the cover)",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)
    if file is not None and not file.is_file():
        typer.secho(f"File not found: {file}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    settings = get_settings()
    api_url = (api_url or settings.api_base_url).rstrip("/")
    admin_key = admin_key or settings.admin_api_key

    with httpx.Client(base_url=api_url, headers={"X-Admin-Key": admin_key}, timeout=30.0) as client:
        if undo:
            response = client.delete(f"/v1/admin/events/{event}/cover")
        else:
            assert file is not None
            content_type = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
            with file.open("rb") as fh:
                response = client.post(
                    f"/v1/admin/events/{event}/cover",
                    files={"file": (file.name, fh, content_type)},
                )

    if response.status_code == 404:
        typer.secho(f"Event {event!r} not found", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    if response.is_error:
        typer.secho(
            f"Could not update cover: {response.status_code} {response.text}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    verb = "Removed" if undo else "Set"
    typer.secho(f"{verb} cover for {event!r}", fg=typer.colors.GREEN)
