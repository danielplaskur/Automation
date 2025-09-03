# OCR-to-Vocab (German → English)

A small Python tool that continuously OCRs a user-selected screen region, translates **whole sentences** German→English using a local WikDict SQLite database, and builds a frequency list from the captured sentences.

## What it does

- Lets you pick a screen rectangle (top-left, bottom-right with your mouse + Enter).
- Every ~1.5s: screenshot → **preprocess** (autocontrast, upscale, unsharp, optional auto‑invert for white text on black) → Tesseract OCR (`deu+eng` by default).
- **Sentence engine:** accumulates text across frames; when a sentence ends with `.` or `?`, prints:
  ```
  Original sentence
  => Translated sentence
  ```
- **Word translation logic:** each token is looked up in WikDict; unknown words remain unchanged; when multiple translations exist, the **first** variant before `|` is used; casing is preserved.
- **Persistence:** each original sentence is appended to `session.txt` (one sentence per line).
- On `Ctrl+C` the tool reads `session.txt` and writes `words.csv` with **frequency,word,translation**.
- With `--debug`, raw and preprocessed screenshots are saved into `debug/` with timestamps.

## Quick start

### 1) Prerequisites
- **Python 3.9+**
- **Tesseract OCR** engine + languages
  - macOS: `brew install tesseract tesseract-lang`
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng`
  - Windows: Install UB Mannheim builds; ensure `tesseract.exe` is on PATH
- **Screen capture permissions**
  - macOS: System Settings → Privacy & Security → Screen Recording + Accessibility → allow your terminal/IDE

### 2) Get the dictionary
Download the German→English SQLite DB from WikDict and place it **next to the script** as `de-en.sqlite3`.

### 3) Install Python deps
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4) Run
```bash
python main.py [FLAGS]
```
Follow the prompts:
1) Place mouse at **top-left** of the region → press **Enter**  
2) Place mouse at **bottom-right** → press **Enter**  
Press **Ctrl+C** to stop and produce `words.csv`.

**Examples**
```bash
# Default languages (deu+eng), automatic invert for dark backgrounds
python main.py

# German only, keep original polarity (disable auto-invert), save debug captures
python main.py --deu-only --no-auto-invert --debug

# Tighter layout assumptions and bigger scale for small fonts
python main.py --psm 6 --scale 3.0
```

## CLI options

| Flag | Default | Description |
|---|---:|---|
| `--debug` | off | Save raw and preprocessed screenshots to `debug/` with timestamps. |
| `--psm <int>` | `6` | Tesseract page segmentation mode. Useful: `3` block, `6` uniform block, `7` single line, `13` raw. |
| `--oem <int>` | `3` | OCR engine mode (`1` LSTM only, `3` default). |
| `--scale <float>` | `2.0` | Upscale factor before OCR to separate glyphs. |
| `--whitelist` | off | Restrict characters to letters/umlauts/ß/digits/punctuation; preserves spaces. |
| `--deu-only` | off | Use `deu` only instead of `deu+eng`. |
| `--no-auto-invert` | off | Disable automatic invert for white-on-black sources. |

## Files and paths

All paths are **relative to the script directory** (`BASE_DIR`). Place `de-en.sqlite3` in the same folder as `main.py`.

- `de-en.sqlite3` — WikDict German→English SQLite DB
- `session.txt` — original sentences captured, one per line
- `words.csv` — frequency list generated from `session.txt` on exit
- `debug/` — optional debug captures: `capture_YYYYmmdd_HHMMSS_ms.png` and `_prep.png`

## Output

`words.csv` columns:

| frequency | word | translation |
|---:|---|---|
| 12 | **beispiel** | "example | model | instance" |
| 5  | **häuser**   | "houses | buildings" |

Notes:
- Translations come from `translation` where `is_good = 1`, highest `score` first; when multiple exist, only the **first** variant is used for word-by-word sentence translation.
- Unknown tokens are left as-is to preserve readability.

## How it works

- **Region selection:** two mouse positions via PyAutoGUI → normalized to `(left, top, width, height)`.
- **Preprocessing:** convert to grayscale → **auto-invert** if mean luminance < 128 → autocontrast → upscale → unsharp mask.
- **OCR:** `pytesseract.image_to_string(..., lang="deu+eng", config="--psm 6 --oem 3" + optional flags)`.
- **Sentences:** text normalized and accumulated across frames; once a terminator `.` or `?` appears, the sentence is translated and printed once; duplicates are suppressed.
- **Frequencies:** on exit, words are extracted from `session.txt` and counted with `collections.Counter`.

## Tips & Troubleshooting

- macOS permissions: re-grant Screen Recording + Accessibility after OS or IDE updates.
- If "m" is misread as "n", try increasing `--scale`, switching `--psm` (6 ↔︎ 3), or enabling `--whitelist`.
- White-on-black sources: leave default auto-invert on; black-on-white: consider `--no-auto-invert`.
- Use `--debug` and inspect the `_prep.png` images to tune flags for your content.

## License

MIT (or your preference). Add a `LICENSE` file if needed.

## Acknowledgements

- Dictionary data: **WikDict** (CC-BY-SA/varies by source).  
- OCR: **Tesseract**.  
- Screenshots & input: **PyAutoGUI**.
