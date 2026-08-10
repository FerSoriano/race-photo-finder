"""The `rpf` command.

Two steps, matching the real-world workflow:
    rpf detect <folder> --event <slug>     # race day, offline
    rpf upload --event <slug> --manifest … # back at the office, online
"""

from __future__ import annotations

import typer

from rpf.cli.detect import detect
from rpf.cli.upload import upload

app = typer.Typer(
    help="Race Photo Finder tools.",
    no_args_is_help=True,
    add_completion=False,
)
app.command("detect")(detect)
app.command("upload")(upload)


if __name__ == "__main__":
    app()
