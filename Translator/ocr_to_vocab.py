#!/usr/bin/env python3
import re
import time
import argparse
from datetime import datetime
import sqlite3
import pyautogui
import pytesseract
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter, ImageStat
from collections import Counter

# ---------------- Configuration ----------------
# WIKDICT_URL = "https://download.wikdict.com/dictionaries/sqlite/2_2025-08/de-en.sqlite3"
# 'lexentry', 'sense_num', 'sense', 'written_rep', 'trans_list', 'score', 'is_good', 'importance'
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "de-en.sqlite3"
OUTPUT_CSV = BASE_DIR / "words.csv"
SESSION_FILE = BASE_DIR / "session.txt"

# Auto OCR configuration
OCR_INTERVAL_SEC = 1.5   # how often to OCR the region
SKIP_IF_NO_CHANGE = True # skip output if OCR text unchanged from last capture

# Tesseract language pack (German)
TESS_LANG = "deu+eng"  # tesseract uses ISO-639-2: 'deu' (German) + 'eng' (English)

# Tokenization: keep letters incl. German umlauts and ß, allow hyphenated compounds
WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß\-]{2,}", re.UNICODE)

# Split sentences on common German punctuation and newlines
SENT_SPLIT_RE = re.compile(r"[\n\r]+|(?<=[\.!?…])\s+")

def extract_words_from_text(text: str):
    words = []
    for w in WORD_RE.findall(text):
        w = w.strip("-").lower()
        if len(w) >= 2:
            words.append(w)
    return words

def prompt_region():
    print("Place the mouse at the TOP-LEFT corner of the region, then press Enter.")
    input()
    x1, y1 = pyautogui.position()
    print(f"Captured top-left: ({x1}, {y1})")

    print("Now place the mouse at the BOTTOM-RIGHT corner of the region, then press Enter.")
    input()
    x2, y2 = pyautogui.position()
    print(f"Captured bottom-right: ({x2}, {y2})")

    # normalize
    left, top = min(x1, x2), min(y1, y2)
    width, height = abs(x2 - x1), abs(y2 - y1)
    if width < 5 or height < 5:
        raise ValueError("Selected region is too small.")
    print(f"Using region: left={left}, top={top}, width={width}, height={height}\n")
    return (left, top, width, height)


def preprocess_for_ocr(img: Image.Image, scale: float = 2.0, auto_invert: bool = True) -> Image.Image:
    g = img.convert("L")
    # If background is dark (white text on black), invert to black text on white
    if auto_invert:
        try:
            mean = ImageStat.ImageStat(g).mean[0]
            if mean < 128:
                g = ImageOps.invert(g)
        except Exception:
            pass
    # Improve contrast slightly
    g = ImageOps.autocontrast(g, cutoff=1)
    # Upscale for better character separation
    if scale and scale != 1.0:
        w, h = g.size
        g = g.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    # Unsharp mask for crisper glyph edges
    try:
        g = g.filter(ImageFilter.UnsharpMask(radius=1.2, percent=150, threshold=3))
    except Exception:
        g = g.filter(ImageFilter.SHARPEN)
    return g


def ocr_region(region, debug_path=None, config: str = None, lang: str = TESS_LANG, scale: float = 2.0, auto_invert: bool = True):
    # Screenshot
    img: Image.Image = pyautogui.screenshot(region=region)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    # Save raw capture if debugging
    if debug_path:
        try:
            Path(debug_path).mkdir(parents=True, exist_ok=True)
            img.save(Path(debug_path) / f"capture_{ts}.png")
        except Exception as e:
            print(f"Debug save failed: {e}")
    # Preprocess for OCR
    pimg = preprocess_for_ocr(img, scale=scale, auto_invert=auto_invert)
    if debug_path:
        try:
            pimg.save(Path(debug_path) / f"capture_{ts}_prep.png")
        except Exception as e:
            print(f"Debug save failed: {e}")
    # OCR
    cfg = config if config is not None else "--psm 6 --oem 3"
    text = pytesseract.image_to_string(pimg, lang=lang, config=cfg)
    return text


def get_translations_for_word_exact(db_path: Path, word: str):
    sql_eq = (
        "SELECT trans_list, score FROM translation "
        "WHERE is_good = 1 AND lower(written_rep) = lower(?) "
        "ORDER BY score DESC LIMIT 1;"
    )
    con = sqlite3.connect(str(db_path))
    try:
        cur = con.cursor()
        cur.execute(sql_eq, (word,))
        row = cur.fetchone()
        if row is None:
            return []
        return row[0]
    finally:
        con.close()


def get_first_translation(db_path: Path, word: str):
    res = get_translations_for_word_exact(db_path, word)
    if not res:
        return None
    # `res` is expected to be a string with variants like "a | b | c"
    if isinstance(res, list):
        s = res[0] if res else None
    else:
        s = res
    if not s:
        return None
    first = s.split("|")[0].strip()
    return first if first else None


def preserve_case(src: str, dst: str) -> str:
    if not dst:
        return dst
    if src.isupper():
        return dst.upper()
    if src[0].isupper():
        return dst[0].upper() + dst[1:]
    return dst


def translate_sentence(db_path: Path, sentence: str) -> str:
    def repl(m: re.Match):
        token = m.group(0)
        t = get_first_translation(db_path, token)
        if not t:
            return token  # leave unknown words as-is
        return preserve_case(token, t)

    return WORD_RE.sub(repl, sentence)


def extract_complete_sentences(text: str):
    # Split text into sentences and return only those that end with '.' or '?'
    parts = [s.strip() for s in SENT_SPLIT_RE.split(text) if s.strip()]
    return [s for s in parts if s.endswith('.') or s.endswith('?')]


def normalize_for_sentence_accum(text: str) -> str:
    # Collapse newlines and repeated whitespace to single spaces for stable accumulation
    return re.sub(r"[\s\r\n]+", " ", text).strip()


def completed_sentences_and_remainder(text: str):
    """
    Return (completed_sentences, remainder). Completed sentences end with '.' or '?'.
    The remainder is the trailing fragment after the last terminator.
    """
    if not text:
        return [], ""
    end = max(text.rfind("."), text.rfind("?"))
    if end == -1:
        return [], text.strip()
    completed_chunk = text[: end + 1]
    remainder = text[end + 1 :].strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", completed_chunk) if s.strip()]
    return sentences, remainder


def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--debug", action="store_true", help="Save captured region images to debug/ with timestamps")
        parser.add_argument("--psm", type=int, default=3, help="Tesseract page segmentation mode (3, 6, 7, 13). Default 3")
        parser.add_argument("--oem", type=int, default=3, help="Tesseract OCR engine mode (1=LSTM only, 3=Default). Default 3")
        parser.add_argument("--scale", type=float, default=2.0, help="Upscale factor before OCR. Default 2.0")
        parser.add_argument("--whitelist", action="store_true", help="Restrict characters to letters, umlauts, ß, digits, common punctuation")
        parser.add_argument("--deu-only", action="store_true", help="Use German language only for OCR")
        parser.add_argument("--no-auto-invert", action="store_true", help="Disable automatic invert when background is dark")
        args = parser.parse_args()
        debug = args.debug
        debug_dir = (Path(OUTPUT_CSV).parent / "debug") if debug else None
        ocr_lang = "deu" if args.deu_only else TESS_LANG
        ocr_cfg = f"--psm {args.psm} --oem {args.oem}"
        if args.whitelist:
            # Include space in whitelist; quote the value and preserve interword spaces
            wl = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÄÖÜäöüß0123456789.,;:()[]-?!%+/ "
            ocr_cfg += f' -c tessedit_char_whitelist="{wl}" -c preserve_interword_spaces=1'
        ocr_scale = args.scale
        auto_invert = not args.no_auto_invert
        region = prompt_region()
        last_text = ""
        seen_words = set()
        all_words = list()
        seen_sentences = set()
        carry = ""
        while True:
            text = ocr_region(region, debug_dir, config=ocr_cfg, lang=ocr_lang, scale=ocr_scale, auto_invert=auto_invert)
            if not text or not text.strip():
                time.sleep(OCR_INTERVAL_SEC)
                continue

            if SKIP_IF_NO_CHANGE and text == last_text:
                time.sleep(OCR_INTERVAL_SEC)
                continue

            last_text = text
            # Accumulate text across OCR frames until a sentence terminator appears
            cleaned = normalize_for_sentence_accum(last_text)
            batch = f"{carry} {cleaned}".strip() if carry else cleaned
            completed, carry = completed_sentences_and_remainder(batch)
            new_sentences = [s for s in completed if s not in seen_sentences]
            if new_sentences:
                # Translate and print all newly seen complete sentences in order
                for s in new_sentences:
                    translated = translate_sentence(DB_PATH, s)
                    print(f"{s}\n=> {translated}\n")
                # Append only originals to session.txt, one per line
                try:
                    with open(SESSION_FILE, "a", encoding="utf-8") as sf:
                        for s in new_sentences:
                            sf.write(f"{s}\n")
                except Exception as e:
                    print(f"Session write failed: {e}")
                for s in new_sentences:
                    seen_sentences.add(s)

            for w in extract_words_from_text(last_text):
                all_words.append(w)
                if w in seen_words:
                    continue
                seen_words.add(w)
                # no per-word output; sentence-level translation happens above
            
            time.sleep(OCR_INTERVAL_SEC)
    except KeyboardInterrupt:
        print("\nStopping… analyzing collected sentences.\n")
        # Build frequency from session.txt instead of in-memory OCR frames
        session_text = ""
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as sf:
                session_text = sf.read()
        except FileNotFoundError:
            session_text = ""
        words_from_session = extract_words_from_text(session_text)
        counter = Counter(words_from_session)
        with open(OUTPUT_CSV, "w", encoding="utf-8") as f:
            f.write("frequency,word,translation\n")
            for word, freq in counter.most_common():
                translations = get_translations_for_word_exact(DB_PATH, word)
                if isinstance(translations, list):
                    translations = " | ".join(translations)
                f.write(f"{freq},{word},\"{translations}\"\n")


if __name__ == "__main__":
    main()
