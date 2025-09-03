#!/usr/bin/env python3
import re
import time
import sqlite3
import pyautogui
import pytesseract
from pathlib import Path
from PIL import Image
from collections import Counter

# ---------------- Configuration ----------------
# WIKDICT_URL = "https://download.wikdict.com/dictionaries/sqlite/2_2025-08/de-en.sqlite3"
# 'lexentry', 'sense_num', 'sense', 'written_rep', 'trans_list', 'score', 'is_good', 'importance'
DB_PATH = "de-en.sqlite3"
OUTPUT_CSV = "words.csv"

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


def ocr_region(region):
    # pyautogui.screenshot(region=(left, top, width, height))
    img: Image.Image = pyautogui.screenshot(region=region)
    # Light preprocessing: convert to grayscale; let Tesseract handle thresholding
    img = img.convert("L")
    # OCR in German
    text = pytesseract.image_to_string(img, lang=TESS_LANG, config="--psm 6")
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


def main():
    try:
        region = prompt_region()
        last_text = ""
        seen_words = set()
        all_words = list()
        while True:
            text = ocr_region(region)
            if not text or not text.strip():
                time.sleep(OCR_INTERVAL_SEC)
                continue

            if SKIP_IF_NO_CHANGE and text == last_text:
                time.sleep(OCR_INTERVAL_SEC)
                continue

            last_text = text
            for w in extract_words_from_text(last_text):
                all_words.append(w)
                if w in seen_words:
                    continue
                seen_words.add(w)
                word = get_translations_for_word_exact(DB_PATH, w)
                if word:
                    print(f"{w} -> {word}")
            
            time.sleep(OCR_INTERVAL_SEC)
    except KeyboardInterrupt:
        print("\nStopping… analyzing collected sentences.\n")
        counter = Counter(all_words)
        with open(OUTPUT_CSV, "w", encoding="utf-8") as f:
            f.write("frequency,word,translation\n")
            for word, freq in counter.most_common():
                translations = get_translations_for_word_exact(DB_PATH, word)
                if isinstance(translations, list):
                    translations = " | ".join(translations)
                f.write(f"{freq},{word},\"{translations}\"\n")


if __name__ == "__main__":
    main()
