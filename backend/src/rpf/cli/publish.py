"""`rpf publish` -- flip an event's visibility.

Office step 5: after verifying photo_count and spot-checking a bib (see
docs/WORKFLOW.md), this makes the event visible on the public API. `--undo`
does the reverse, e.g. to pull an event back while fixing a mistake.
"""

from __future__ import annotations

from typing import Annotated

import httpx
import typer

from rpf.config import get_settings

app = typer.Typer(help="Publish or unpublish an event.")


@app.command()
def publish(
    event: Annotated[str, typer.Option("--event", "-e", help="Event slug")],
    undo: Annotated[bool, typer.Option("--undo", help="Unpublish instead of publish")] = False,
    api_url: Annotated[str | None, typer.Option("--api-url", help="API base URL")] = None,
    admin_key: Annotated[str | None, typer.Option("--admin-key", help="X-Admin-Key")] = None,
) -> None:
    settings = get_settings()
    api_url = (api_url or settings.api_base_url).rstrip("/")
    admin_key = admin_key or settings.admin_api_key

    with httpx.Client(base_url=api_url, headers={"X-Admin-Key": admin_key}, timeout=30.0) as client:
        response = client.patch(f"/v1/admin/events/{event}", json={"is_published": not undo})

    if response.status_code == 404:
        typer.secho(f"Event {event!r} not found", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    if response.is_error:
        typer.secho(
            f"Could not update event: {response.status_code} {response.text}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    verb = "Unpublished" if undo else "Published"
    typer.secho(f"{verb} {event!r}", fg=typer.colors.GREEN)
