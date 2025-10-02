#!/usr/bin/env python3
"""
Clean OCR duplicates from session file.

This script processes a session file containing team communication to:
1. Remove duplicate conversation blocks
2. Clean up incomplete sentences from bad OCR
3. Preserve speaker-name structure
4. Exclude usernames from frequency analysis
"""

import re
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

speaker_patterns = [
    r'^(Jonathan Spill \d+ [A-Z]+)$'
]

conversation_blocks = []
seen_blocks = set()

def extract_speaker_names(text):
    """Extract speaker names from the text."""
    # More specific patterns for actual speaker names (German names typically)
    speakers = []
    for pattern in speaker_patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        speakers.extend(matches)

    return speakers

def is_speaker_line(line):
    """Check if a line contains a speaker name."""
    # Use the same specific patterns as extract_speaker_names
    return any(re.match(pattern, line.strip()) for pattern in speaker_patterns)

def clean_incomplete_sentences(text):
    """Clean up incomplete sentences from bad OCR."""
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip speaker lines
        if is_speaker_line(line):
            cleaned_lines.append(line)
            continue

        # Fix common OCR issues
        # Remove incomplete words at the end of lines that don't end with punctuation
        if line and not line.endswith(('.', '!', '?', ',', ':', ';')):
            # Check if line ends with incomplete word (no punctuation and not a complete sentence)
            words = line.split()
            if words and len(words[-1]) <= 3:  # Very short last word might be incomplete
                # Remove the incomplete word
                line = ' '.join(words[:-1])
                if line and not line.endswith(('.', '!', '?', ',', ':', ';')):
                    line += '.'

        # Remove very short lines that are likely OCR artifacts
        if line and len(line) < 10:
            # Check if it's just fragments like "Also dass" or "Ja, aber das"
            if re.match(r'^(also|ja|nein|nee|aber|und|oder|dass|das|die|der|den|dem)\.?$', line.lower()):
                continue

        if line:  # Only add non-empty lines
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)

def normalize_text(text):
    """Normalize text for better duplicate comparison."""
    # Remove extra whitespace and normalize punctuation
    normalized = re.sub(r'\s+', ' ', text.strip())
    # Remove minor punctuation differences that might be OCR artifacts
    normalized = re.sub(r'[,.]*$', '', normalized)  # Remove trailing commas/periods
    return normalized.lower()

def calculate_similarity(text1, text2):
    """Calculate similarity ratio between two texts."""
    # Simple similarity based on common words
    words1 = set(text1.split())
    words2 = set(text2.split())

    if not words1 or not words2:
        return 0.0

    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))

    return intersection / union if union > 0 else 0.0

def remove_duplicates(text):
    """Remove duplicate conversation blocks."""
    lines = text.split('\n')
    cleaned_lines = []
    current_block = []
    last_speaker = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Check if this is a speaker line
        if is_speaker_line(line):
            # If we have a previous block, check if it's a duplicate
            if current_block and last_speaker:
                block_text = '\n'.join(current_block)

                # Check for exact duplicates first
                is_duplicate = False
                for seen_block in seen_blocks:
                    if block_text == seen_block:
                        is_duplicate = True
                        break

                # If no exact match, check for similarity
                if not is_duplicate:
                    for seen_block in seen_blocks:
                        similarity = calculate_similarity(
                            normalize_text(block_text),
                            normalize_text(seen_block)
                        )
                        if similarity > 0.7:  # 70% similarity threshold
                            is_duplicate = True
                            break

                if is_duplicate:
                    # Skip this duplicate block
                    i += len(current_block)
                    current_block = [line]
                    last_speaker = line
                    continue
                else:
                    # Add the previous block to seen blocks
                    seen_blocks.add(block_text)

            # Start new block
            if current_block:
                cleaned_lines.extend(current_block)
            current_block = [line]
            last_speaker = line
        else:
            # Add content line to current block
            current_block.append(line)

        i += 1

    # Add the last block
    if current_block:
        block_text = '\n'.join(current_block)

        # Check for exact duplicates first
        is_duplicate = False
        for seen_block in seen_blocks:
            if block_text == seen_block:
                is_duplicate = True
                break

        # If no exact match, check for similarity
        if not is_duplicate:
            for seen_block in seen_blocks:
                similarity = calculate_similarity(
                    normalize_text(block_text),
                    normalize_text(seen_block)
                )
                if similarity > 0.7:  # 70% similarity threshold
                    is_duplicate = True
                    break

        if not is_duplicate:
            cleaned_lines.extend(current_block)

    return '\n'.join(cleaned_lines)

def process_session(full_path):
    """Main processing function."""
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Step 1: Remove duplicates
        content_no_duplicates = remove_duplicates(content)
        # Step 2: Clean incomplete sentences
        cleaned_content = clean_incomplete_sentences(content_no_duplicates)
        # Step 3: Save cleaned content
        # name should be cleaned_<session_id>.txt
        session_id = os.path.splitext(os.path.basename(full_path))[0]
        output_file = os.path.join(os.path.dirname(full_path), f"cleaned_{session_id}.txt")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)

        return True

    except FileNotFoundError:
        print(f"Error: File '{full_path}' not found.")
        return False
    except Exception as e:
        print(f"Error processing file: {e}")
        return False

def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    # if there is an argument clean only that file otherwise clean all
    if len(sys.argv) > 1:
        # Clean only the specified file
        full_path = os.path.join(base_path, sys.argv[1])
        process_session(full_path)
    else:
        for file_path in os.listdir(base_path):
            if file_path.startswith("session"):
                full_path = os.path.join(base_path, file_path)
                process_session(full_path)

if __name__ == "__main__":
    main()
