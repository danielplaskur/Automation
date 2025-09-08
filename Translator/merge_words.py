#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import glob
import os
import re
import sys
from collections import defaultdict

SPLIT_RX = re.compile(r"\s*\|\s*")  # na delenie prekladov podľa ' | '

def parse_int(value):
    try:
        return int(str(value).strip())
    except Exception:
        return 0

def normalize_word(word, case_insensitive=False):
    w = (word or "").strip()
    return w.lower() if case_insensitive else w

def collect_from_file(path, acc, *,
                      case_insensitive=False,
                      split_translations=True,
                      verbose=True):
    """
    acc: dict[word] -> {'freq': int, 'translations': set[str]}
    """
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            # over stĺpce (tolerantne)
            field_map = {k.strip().lower(): k for k in reader.fieldnames or []}
            required = ["frequency", "word", "translation"]
            if not all(col in field_map for col in required):
                if verbose:
                    print(f"UPOZORNENIE: Súbor '{path}' preskakujem – chýbajú stĺpce "
                          f"(potrebné: {required}, našiel som: {reader.fieldnames})")
                return 0, 0

            freq_key = field_map["frequency"]
            word_key = field_map["word"]
            trans_key = field_map["translation"]

            rows = 0
            kept = 0
            for row in reader:
                rows += 1
                word = normalize_word(row.get(word_key, ""), case_insensitive=case_insensitive)
                if not word:
                    continue
                freq = parse_int(row.get(freq_key, 0))

                raw_tr = (row.get(trans_key, "") or "").strip()
                parts = []
                if raw_tr:
                    if split_translations:
                        parts = [p.strip() for p in SPLIT_RX.split(raw_tr) if p.strip()]
                    else:
                        parts = [raw_tr]

                bucket = acc[word]
                bucket["freq"] += freq
                for p in parts:
                    bucket["translations"].add(p)

                kept += 1

            return rows, kept
    except FileNotFoundError:
        if verbose:
            print(f"Súbor '{path}' neexistuje.")
        return 0, 0
    except Exception as e:
        print(f"CHYBA: Nepodarilo sa spracovať '{path}': {e}")
        return 0, 0

def write_output(path, acc, *, encoding="utf-8"):
    # zoradenie: najprv podľa frekvencie (desc), potom abecedne podľa slova
    items = sorted(
        ((word, data["freq"], " | ".join(sorted(data["translations"])) if data["translations"] else "")
         for word, data in acc.items()),
        key=lambda x: (-x[1], x[0]),
    )
    with open(path, "w", encoding=encoding, newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frequency", "word", "translation"])
        for word, freq, tr in items:
            writer.writerow([freq, word, tr])
    return len(items)

def main():
    ap = argparse.ArgumentParser(
        description="Spojí všetky words_*.csv do words.csv s kumulovanými frekvenciami."
    )
    ap.add_argument("--dir", default=".", help="Adresár, kde hľadať vstupné súbory (default: .)")
    ap.add_argument("--pattern", default="words_*.csv", help="Vzor súborov (default: words_*.csv)")
    ap.add_argument("--out", default="words.csv", help="Výstupný súbor (default: words.csv)")
    ap.add_argument("--case-insensitive", action="store_true",
                    help="Agregovať bez ohľadu na veľkosť písmen (word -> word.lower()).")
    ap.add_argument("--keep-joined-translation", action="store_true",
                    help="Nedeliť existujúce preklady podľa '|', iba ich brať ako celok.")
    ap.add_argument("--quiet", action="store_true", help="Menej výpisov.")
    args = ap.parse_args()

    search_glob = os.path.join(args.dir, args.pattern)
    files = sorted(glob.glob(search_glob))
    if not files:
        print(f"Nenašiel som žiadne súbory podľa: {search_glob}")
        sys.exit(1)

    if not args.quiet:
        print(f"Nájdené súbory ({len(files)}):")
        for f in files:
            print(" -", os.path.relpath(f))

    acc = defaultdict(lambda: {"freq": 0, "translations": set()})
    total_rows = 0
    total_kept = 0
    for f in files:
        rows, kept = collect_from_file(
            f,
            acc,
            case_insensitive=args.case_insensitive,
            split_translations=not args.keep_joined_translation,
            verbose=not args.quiet
        )
        total_rows += rows
        total_kept += kept

    out_path = os.path.join(args.dir, args.out)
    n_items = write_output(out_path, acc)
    # Remove the input files (subfiles) that were merged, leaving only the main output
    removed = 0
    removed_errors = []
    try:
        abs_out = os.path.abspath(out_path)
        for f in files:
            try:
                # skip removing the output file itself if it happens to match
                if os.path.abspath(f) == abs_out:
                    continue
                os.remove(f)
                removed += 1
            except Exception as e:
                removed_errors.append((f, str(e)))
    except Exception as e:
        removed_errors.append(("glob_loop", str(e)))

    if not args.quiet:
        print("\nHotovo.")
        print(f" Spracovaných záznamov:  {total_rows}")
        print(f" Prevzatých záznamov:   {total_kept}")
        print(f" Unikátnych slov:       {n_items}")
        print(f" Výstup:                {out_path}")
        print(f" Odstránené pod-súbory: {removed}")
        if removed_errors:
            print(" Niektoré súbory sa nepodarilo odstrániť:")
            for fn, err in removed_errors:
                print(f"  - {fn}: {err}")

if __name__ == "__main__":
    main()
