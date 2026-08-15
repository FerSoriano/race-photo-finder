"""`rpf create-event` -- create an event with no photos yet.

Lets an event slug exist ahead of race day (e.g. to set a cover image or
announce it early) without needing a manifest. `rpf upload --create-event`
does this implicitly; this command is for when there is nothing to upload yet.
"""

from __future__ import annotations

from typing import Annotated

import httpx
import typer

from rpf.config import get_settings

app = typer.Typer(help="Create an event with no photos yet.")


@app.command()
def create_event(
    slug: Annotated[str, typer.Argument(help="Event slug (lowercase, hyphen-separated)")],
    name: Annotated[str, typer.Option("--name", "-n", help="Event display name")],
    event_date: Annotated[
        str | None, typer.Option("--date", help="Event date (YYYY-MM-DD)")
    ] = None,
    location: Annotated[str | None, typer.Option("--location", help="Event location")] = None,
    description: Annotated[
        str | None, typer.Option("--description", help="Event description")
    ] = None,
    publish: Annotated[
        bool, typer.Option("--publish", help="Publish immediately instead of leaving a draft")
    ] = False,
    api_url: Annotated[str | None, typer.Option("--api-url", help="API base URL")] = None,
    admin_key: Annotated[str | None, typer.Option("--admin-key", help="X-Admin-Key")] = None,
) -> None:
    settings = get_settings()
    api_url = (api_url or settings.api_base_url).rstrip("/")
    admin_key = admin_key or settings.admin_api_key

    payload = {
        "slug": slug,
        "name": name,
        "event_date": event_date,
        "location": location,
        "description": description,
        "is_published": publish,
    }

    with httpx.Client(base_url=api_url, headers={"X-Admin-Key": admin_key}, timeout=30.0) as client:
        response = client.post("/v1/admin/events", json=payload)

    if response.status_code == 409:
        typer.secho(f"Event {slug!r} already exists", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    if response.is_error:
        typer.secho(
            f"Could not create event: {response.status_code} {response.text}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    typer.secho(f"Created event {slug!r}", fg=typer.colors.GREEN)
    typer.echo(f"Next: rpf detect <folder> --event {slug}")
