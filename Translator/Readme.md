# OCR-to-Vocab (German → English)

A tiny Python utility that OCRs a user-selected screen region on a loop, extracts German words, looks up translations from a local WikDict SQLite database, prints live matches, and on exit writes a frequency-sorted CSV (`words.csv`) for study.

## What it does

- Lets you pick a screen rectangle (top-left, bottom-right with your mouse + Enter).
- Every ~1.5s: screenshots that region → OCR (Tesseract `deu+eng`) → tokenizes words (incl. umlauts/ß).
- For each unique word, queries a local WikDict SQLite (`de-en.sqlite3`) and prints its best translation.
- On `Ctrl+C`: aggregates all seen words, writes `words.csv` with `frequency,word,translation`.

---

## Quick start

### 1) Prerequisites
- **Python 3.9+**
- **Tesseract OCR** engine
  - macOS: `brew install tesseract tesseract-lang`
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr tesseract-ocr-deu`
  - Windows: Install from UB Mannheim builds; ensure `tesseract.exe` is on PATH
- **Screen capture permissions**
  - macOS: System Settings → Privacy & Security → Screen Recording + Accessibility → allow your terminal/IDE
  - Windows: If using admin/UAC prompts, allow screen capture
  - X11/Wayland: ensure your DE allows screenshots

### 2) Get the dictionary
Download the German→English SQLite DB from WikDict and place it next to the script as `de-en.sqlite3`.

> Example source (update to latest):
> https://download.wikdict.com/dictionaries/sqlite/2_2025-08/de-en.sqlite3

### 3) Install Python deps
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install pyautogui pytesseract pillow

sqlite3 and re are in the standard library.

# OCR-to-Vocab (German → English)

A tiny Python utility that OCRs a user-selected screen region on a loop, extracts German words, looks up translations from a local WikDict SQLite database, prints live matches, and on exit writes a frequency-sorted CSV (`words.csv`) for study.

## What it does

- Lets you pick a screen rectangle (top-left, bottom-right with your mouse + Enter).
- Every ~1.5s: screenshots that region → OCR (Tesseract `deu+eng`) → tokenizes words (incl. umlauts/ß).
- For each unique word, queries a local WikDict SQLite (`de-en.sqlite3`) and prints its best translation.
- On `Ctrl+C`: aggregates all seen words, writes `words.csv` with `frequency,word,translation`.

---

## Quick start

### 1) Prerequisites
- **Python 3.9+**
- **Tesseract OCR** engine
  - macOS: `brew install tesseract tesseract-lang`
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr tesseract-ocr-deu`
  - Windows: Install from UB Mannheim builds; ensure `tesseract.exe` is on PATH
- **Screen capture permissions**
  - macOS: System Settings → Privacy & Security → Screen Recording + Accessibility → allow your terminal/IDE
  - Windows: If using admin/UAC prompts, allow screen capture
  - X11/Wayland: ensure your DE allows screenshots

### 2) Get the dictionary
Download the German→English SQLite DB from WikDict and place it next to the script as `de-en.sqlite3`.

> Example source (update to latest):
```
https://download.wikdict.com/dictionaries/sqlite/2_2025-08/de-en.sqlite3
```

### 3) Install Python deps
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> `sqlite3` and `re` are in the standard library.

### 4) Run
```bash
python ocr_to_vocab.py
```
Follow the prompts:
1) Place mouse at **top-left** of the region → press **Enter**  
2) Place mouse at **bottom-right** → press **Enter**  
Let it run. Press **Ctrl+C** to stop and produce `words.csv`.

---

## Configuration

Edit the constants at the top of the script:

| Name | Default | Description |
|---|---:|---|
| `DB_PATH` | `"de-en.sqlite3"` | Path to the WikDict SQLite db. |
| `OUTPUT_CSV` | `"words.csv"` | Output CSV filename. |
| `OCR_INTERVAL_SEC` | `1.5` | Polling interval for OCR (in seconds). |
| `SKIP_IF_NO_CHANGE` | `True` | Skip processing if OCR text hasn’t changed. |
| `TESS_LANG` | `"deu+eng"` | Tesseract languages (ISO-639-2 codes). |

### Tokenization
- Keeps letters incl. `ÄÖÜäöüß` and hyphenated compounds.
- Regex: `[A-Za-zÄÖÜäöüß\-]{2,}` (lowercased, trimmed of edge hyphens).

---

## Output

`words.csv` with columns:

| frequency | word | translation |
|---:|---|---|
| 12 | **beispiel** | "example | model | instance" |
| 5  | **häuser**   | "houses | buildings" |

Notes:
- Translations come from the `translation` table where `is_good = 1`, top by `score`.
- If multiple translations are available, they’re joined with ` | `.

---

## How it works (under the hood)

- **Region selection:** Captures two mouse positions via `pyautogui.position()`, normalizes to `(left, top, width, height)`.
- **OCR:** `pyautogui.screenshot(region=...)` → `PIL.Image.convert("L")` → `pytesseract.image_to_string(..., lang="deu+eng", --psm 6)`.
- **Lookup:** SQLite `SELECT trans_list, score FROM translation WHERE is_good=1 AND lower(written_rep)=lower(?) ORDER BY score DESC LIMIT 1;`
- **Exit flow:** On `KeyboardInterrupt`, aggregates frequencies with `collections.Counter` and writes CSV.

---

## Tips & Troubleshooting

- **No text recognized?**
  - Verify Tesseract install: run `tesseract --version`.
  - Ensure `deu` language data is installed (`tesseract-ocr-deu`).
  - Increase contrast/zoom of the target app; dark themes can reduce OCR quality.
  - Try different `--psm` values (e.g., `--psm 6` → assume uniform text block).

- **Permission errors on macOS:** Re-grant Screen Recording + Accessibility for your terminal/IDE after any updates.

- **High CPU usage:** Increase `OCR_INTERVAL_SEC` to reduce polling frequency.

- **Wrong translations or missing words:** WikDict schemas may change. Make sure you’re using a matching, recent DB. Hyphenated edge cases are stripped; compound forms might require stemmed queries (future work).

---

## Security & Privacy

- This script **screenshots your display region** repeatedly. Use only on content you’re comfortable processing locally.
- All processing is local; no network calls after you download the DB.

---

## Roadmap

- Fuzzy/lemmatized lookup when exact `written_rep` is missing.
- Persist per-session cache to avoid duplicate DB hits.
- Optional overlay showing current OCR’d text.
- CLI flags for all config options.
- Anki deck export (APKG/TSV) with frequency thresholds.
- Add stop-words list / POS filtering.

---

## License

MIT (or your preference). Add a `LICENSE` file.

---

## Acknowledgements

- Dictionary data: **WikDict** (CC-BY-SA/varies by source).  
- OCR: **Tesseract**.  
- Screenshots & input: **PyAutoGUI**.
