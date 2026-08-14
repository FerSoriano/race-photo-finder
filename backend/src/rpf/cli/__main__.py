"""The `rpf` command.

Matches the real-world workflow:
    rpf detect <folder> --event <slug>     # race day, offline
    rpf upload --event <slug> --manifest … # back at the office, online
    rpf cover <slug> <file>                # optional: set the event banner
    rpf publish --event <slug>             # make it visible on the public API
"""

from __future__ import annotations

import typer

from rpf.cli.cover import cover
from rpf.cli.detect import detect
from rpf.cli.publish import publish
from rpf.cli.upload import upload

app = typer.Typer(
    help="Race Photo Finder tools.",
    no_args_is_help=True,
    add_completion=False,
)
app.command("detect")(detect)
app.command("upload")(upload)
app.command("publish")(publish)
app.command("cover")(cover)


if __name__ == "__main__":
    app()
