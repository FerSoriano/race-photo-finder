---
name: detect-bibs
description: Run or debug the bib-number detection pipeline over a folder of race photos using the local Ollama vision model. Use when asked to detect/extract runner numbers, process a race folder, work on the detection prompt or parser, or investigate why a bib was missed or misread.
---

# Bib detection

## Run it

```bash
uv --project backend run rpf detect <folder> --event <slug>
```

Writes `<folder>/manifest.json`, saving after every photo. Resumable: re-running
skips finished photos; errored ones are retried. `--force` re-analyzes
everything.

Requires Ollama running with `qwen2.5vl:7b`:

```bash
ollama list | grep qwen2.5vl
```

## Where the code lives

| File | Responsibility |
| --- | --- |
| `detection/base.py` | `BibDetector` protocol, `Bib` dataclass |
| `detection/ollama_detector.py` | the prompt, the model call, `parse_response` |
| `detection/normalize.py` | raw strings → storable bib numbers |
| `detection/manifest.py` | the manifest format, resumability, sha256 |
| `cli/detect.py` | the command, progress, error handling |

Callers depend on the `BibDetector` protocol, so a different model or a
YOLO/OCR pipeline can be swapped in by adding a class with `name` and `detect`.

## The regression check — always run it

The four photos in `samples/photos` have known answers:

| Photo | Expected bibs |
| --- | --- |
| `21k-gdl-3.jpg` | `19131, 6133, 13441` |
| `5e39...medio-maraton.jpeg` | `1, 5` |
| `images (1).jpeg` | `4076, 1578` |
| `images.jpeg` | `6700` |

After **any** change to the prompt, the parser or the normaliser:

```bash
uv --project backend run rpf detect samples/photos --event test-event --force
```

and confirm the output still matches. The model is deterministic here
(`temperature: 0`).

Fast checks that need no model:

```bash
uv --project backend run pytest backend/tests/unit/test_normalize.py -q
```

## Rules when changing detection

- Keep `temperature: 0`. Reproducibility is what makes the table above a test.
- The prompt asks the model to prefix unsure digits with `?`. `normalize.py`
  turns that into `is_uncertain=True` — do not drop the convention on one side
  only.
- `parse_response` falls back to a digit regex when JSON parsing fails. Keep the
  fallback; smaller models drift out of JSON.
- Bib numbers stay **text**. Never cast to int — `0042` and `42` are different
  bibs.
- Plausible length is 1–6 digits (`normalize.py`). Widening it lets sponsor
  banners and shoe logos in.

## Debugging a missed or wrong bib

1. Is it in the raw model output? Call the detector directly on that one photo
   before blaming the parser.
2. In the output but not the manifest? The normaliser dropped it — check length
   bounds and the digit regex.
3. In the manifest but not searchable? That is ingest or search, not detection —
   check `photo_bibs` rows for the photo.
4. Consistently misread digits? That is what the `similar_bibs` fuzzy fallback
   exists for; verify it suggests the right number rather than over-tuning the
   prompt.
