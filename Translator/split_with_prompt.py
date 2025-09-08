#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Iterable, Tuple

# BASE_DIR = umiestnenie tohto skriptu
BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "tmp"

# Tvoj custom prompt (presne podľa zadania), vložený na začiatok každého výstupného súboru
CUSTOM_PROMPT = (
    '{"task":"meeting_summary","instructions":{"language":"English","detail_level":"high",'
    '"structure":[{"section":"Topics Discussed","description":"List and describe all major '
    'points, issues, and subjects that were addressed during the meeting."},{"section":"Resolutions",'
    '"description":"Explain how each issue was resolved or what decisions were made."},{"section":"Next Steps",'
    '"description":"Outline planned actions, responsible persons, and any deadlines or follow-up items."},'
    '{"section":"Unresolved or Unclear Items","description":"Highlight any topics that were not fully resolved or '
    'need further clarification."}]},"input_format":"inline_text","output_format":"structured_text"}'
)


def chunk_text(
    text: str,
    max_chars: int,
    prefer_word_boundary: bool = False,
) -> Iterable[str]:
    """
    Rozdelí text na kúsky s max dĺžkou max_chars (počítané na znaky).
    Ak prefer_word_boundary=True, pokúsi sa deliť na bielych znakoch/nových riadkoch,
    ale nikdy neprekročí max_chars.
    """
    n = len(text)
    i = 0
    while i < n:
        end = min(i + max_chars, n)
        if prefer_word_boundary and end < n:
            # Skúsiť nájsť najbližšie rozumné miesto pred 'end'
            window = text[i:end]
            # Najprv preferuj koniec riadka
            last_nl = window.rfind("\n")
            # Potom medzeru
            last_sp = window.rfind(" ")

            candidate = max(last_nl, last_sp)

            if candidate > 0 and candidate >= int(max_chars * 0.6):
                # Režeme na rozumnom mieste, aspoň 60 % chunku vyplnené
                end = i + candidate + 1  # +1 aby sme neprišli o oddeľovač
        yield text[i:end]
        i = end


def write_chunks_with_prompt(
    input_path: Path,
    chunk_chars: int = 7000,
    prefer_word_boundary: bool = False,
    line_separator: str = "\n",
) -> List[Tuple[Path, int]]:
    """
    Načíta input_path, rozdelí obsah na chunks po 'chunk_chars', a pre každý chunk vytvorí
    výstupný súbor v OUT_DIR s CUSTOM_PROMPT + (line_separator) + chunk.

    Vracia zoznam (output_path, total_chars_written).
    """
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    content = input_path.read_text(encoding="utf-8")
    prompt_len = len(CUSTOM_PROMPT)

    results: List[Tuple[Path, int]] = []
    stem = input_path.stem
    suffix = input_path.suffix or ".txt"

    for idx, chunk in enumerate(
        chunk_text(content, max_chars=chunk_chars, prefer_word_boundary=prefer_word_boundary), start=1
    ):
        # Zloženie výstupného obsahu
        out_text = f"{CUSTOM_PROMPT}{line_separator}{chunk}"
        total_len = len(out_text)

        out_file = OUT_DIR / f"{stem}_part{idx:03d}{suffix}"
        out_file.write_text(out_text, encoding="utf-8")

        results.append((out_file, total_len))

    return results


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Rozdelí vstupný súbor na menšie súbory po N znakov (default 7000) a na začiatok "
            "každého pridá definovaný custom prompt. Výstup sa uloží do tmp/ pri tomto skripte."
        )
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Cesta k vstupnému TXT súboru (napr. session_20250908_090141.txt)",
    )
    parser.add_argument(
        "--chunk",
        type=int,
        default=7000,
        help="Počet znakov obsahu v jednom súbore (bez promptu). Default: 7000",
    )
    parser.add_argument(
        "--word-boundary",
        action="store_true",
        help="Pokúsiť sa deliť na hraniciach slov/riadkov (bez prekročenia limitu).",
    )
    parser.add_argument(
        "--no-empty-line",
        action="store_true",
        help="Nevkladať prázdny riadok medzi prompt a obsah (default vkladá 1 riadok).",
    )

    args = parser.parse_args()

    if not args.input_file.exists():
        raise FileNotFoundError(f"Súbor neexistuje: {args.input_file}")

    line_sep = "" if args.no_empty_line else "\n"

    prompt_len = len(CUSTOM_PROMPT)
    print(f"- Dĺžka custom promptu: {prompt_len} znakov")
    print(f"- Veľkosť chunku (obsah): {args.chunk} znakov")
    print(f"- Očakávaná dĺžka výstupného súboru (prompt + obsah): ~{prompt_len + args.chunk} znakov\n")

    results = write_chunks_with_prompt(
        input_path=args.input_file,
        chunk_chars=args.chunk,
        prefer_word_boundary=args.word_boundary,
        line_separator=line_sep,
    )

    print(f"Vytvorených súborov: {len(results)}")
    for p, total_len in results:
        print(f"  · {p}  (spolu {total_len} znakov)")


if __name__ == "__main__":
    main()
