#!/usr/bin/env python3
"""
Usage:
    python3 extract_numbers.py [folder] [--model qwen2.5vl:7b] [--output results.csv]

By default processes the "photos" folder of the project.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import ollama

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

PROMPT = """Analyze this photo from a race/marathon. Identify the runner \
number (bib number) of each runner visible in the image, even \
if it's blurry, at an angle, or partially visible.

Respond ONLY with valid JSON, with no additional text, in this format:
{"numbers": ["1234", "5678"]}

If you don't see any runner number, respond: {"numbers": []}
If a number is partially visible or you're unsure of a digit, include it \
anyway marking it with a "?" at the start (example: "?234")."""


def list_photos(folder: Path) -> list[Path]:
    return sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS
    )


def extract_numbers_from_response(text: str) -> list[str]:
    """Parses the model's JSON response; falls back to a number regex if it fails."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            numbers = data.get("numbers", [])
            if isinstance(numbers, list):
                return [str(n).strip() for n in numbers if str(n).strip()]
        except json.JSONDecodeError:
            pass
    return re.findall(r"\d{1,6}", text)


def analyze_photo(path: Path, model: str) -> list[str]:
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": PROMPT, "images": [str(path)]}],
        options={"temperature": 0},
    )
    return extract_numbers_from_response(response["message"]["content"])


def main():
    parser = argparse.ArgumentParser(
        description="Extracts runner numbers from photos using a local vision model (Ollama)."
    )
    parser.add_argument("folder", nargs="?", default="images", help="folder with the photos (default: photos)")
    parser.add_argument("--model", default="qwen2.5vl:7b", help="Ollama model to use")
    parser.add_argument("--output", default="results.csv", help="Output CSV file")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        sys.exit(f"Error: folder '{folder}' does not exist")

    photos = list_photos(folder)
    if not photos:
        sys.exit(f"No photos found ({', '.join(sorted(VALID_EXTENSIONS))}) in '{folder}'")

    print(f"Found {len(photos)} photos. Using model '{args.model}'...\n")

    output = Path(f"data/{args.output}")
    all_numbers = set()

    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["photo", "numbers_found"])

        for i, photo in enumerate(photos, 1):
            try:
                numbers = analyze_photo(photo, args.model)
            except Exception as e:
                print(f"[{i}/{len(photos)}] {photo.name}: ERROR ({e})")
                writer.writerow([photo.name, f"ERROR: {e}"])
                f.flush()
                continue

            all_numbers.update(numbers)
            numbers_text = ", ".join(numbers) if numbers else "(none)"
            print(f"[{i}/{len(photos)}] {photo.name}: {numbers_text}")

            writer.writerow([photo.name, "; ".join(numbers)])
            f.flush()

    print(f"\nDone. {len(all_numbers)} unique numbers found in total.")
    print(f"Detailed results (per photo) saved to: {output}")
    print("\nList of all numbers found:")
    for number in sorted(all_numbers):
        print(f"  - {number}")


if __name__ == "__main__":
    main()
