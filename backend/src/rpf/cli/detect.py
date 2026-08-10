"""`rpf detect` -- run bib detection over a folder of race photos.

Race-day step: photos come off the camera, this runs offline against the local
Ollama model and writes a manifest. Nothing here needs the internet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from rpf.config import get_settings
from rpf.detection.manifest import Manifest, PhotoEntry, sha256_of
from rpf.detection.ollama_detector import OllamaBibDetector, list_photos

app = typer.Typer(help="Detect runner bib numbers in photos.")


@app.command()
def detect(
    folder: Annotated[Path, typer.Argument(help="Folder containing the race photos")],
    event: Annotated[str, typer.Option("--event", "-e", help="Event slug")],
    manifest_path: Annotated[
        Path | None,
        typer.Option("--manifest", "-m", help="Manifest file (default: <folder>/manifest.json)"),
    ] = None,
    model: Annotated[str | None, typer.Option("--model", help="Ollama model")] = None,
    force: Annotated[
        bool, typer.Option("--force", help="Re-analyze photos already in the manifest")
    ] = False,
) -> None:
    settings = get_settings()
    model = model or settings.ollama_model

    if not folder.is_dir():
        typer.secho(f"Folder not found: {folder}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    photos = list_photos(folder)
    if not photos:
        typer.secho(f"No photos found in {folder}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    manifest_path = manifest_path or folder / "manifest.json"
    manifest = Manifest.load_or_new(manifest_path, event_slug=event, model=model)
    done = set() if force else manifest.processed_filenames

    pending = [p for p in photos if p.name not in done]
    skipped = len(photos) - len(pending)
    typer.echo(
        f"{len(photos)} photos in {folder} | {skipped} already done | "
        f"{len(pending)} to analyze with '{model}'"
    )

    detector = OllamaBibDetector(model=model, host=settings.ollama_host)

    for i, photo in enumerate(pending, 1):
        prefix = f"[{i}/{len(pending)}] {photo.name}"
        try:
            bibs = detector.detect(photo)
        except Exception as exc:  # keep going; the run resumes on the next pass
            typer.secho(f"{prefix}: ERROR {exc}", fg=typer.colors.RED)
            manifest.add(PhotoEntry(filename=photo.name, sha256="", error=str(exc)))
        else:
            found = ", ".join(f"{b.number}{'?' if b.is_uncertain else ''}" for b in bibs)
            typer.echo(f"{prefix}: {found or '(none)'}")
            manifest.add(PhotoEntry(filename=photo.name, sha256=sha256_of(photo), bibs=bibs))

        # Saved after every photo so a crash never loses more than one result.
        manifest.save(manifest_path)

    ok = [p for p in manifest.photos if p.error is None]
    failed = [p for p in manifest.photos if p.error is not None]
    unique = {b.number for p in ok for b in p.bibs}

    typer.secho(
        f"\nDone. {len(ok)} photos, {len(unique)} unique bibs"
        + (f", {len(failed)} failed" if failed else ""),
        fg=typer.colors.GREEN,
    )
    typer.echo(f"Manifest: {manifest_path}")
    typer.echo(f"Next: rpf upload --event {event} --manifest {manifest_path}")
