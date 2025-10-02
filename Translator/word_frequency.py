#!/usr/bin/env python3
"""
Word Frequency Analyzer
Reads cleaned session file and outputs word frequencies to CSV
"""
import os
import re
from collections import Counter
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clean_word(word):
    """Clean a word by removing special characters and numbers"""
    # Remove special characters and numbers, keep only letters and common word characters
    cleaned = re.sub(r'[^a-zA-ZäöüÄÖÜß]', '', word)
    return cleaned.strip()

def load_whitelist(whitelist_path):
    """Load whitelist from file if it exists"""
    whitelist = set()
    if os.path.exists(whitelist_path):
        try:
            with open(whitelist_path, "r", encoding="utf-8") as f:
                for line in f:
                    # Strip whitespace and comments
                    word = line.strip()
                    if word and not word.startswith("#"):
                        # Clean the word and add to lowercase
                        cleaned = clean_word(word.lower())
                        if cleaned:
                            whitelist.add(cleaned)
        except Exception as e:
            print(f"Warning: Could not load whitelist: {e}")

    return whitelist

def analyze_word_frequency(input_file, output_file, whitelist_file):
    """Analyze word frequency in the input file and merge with existing data"""
    # Load whitelist
    whitelist = load_whitelist(whitelist_file)

    # Read and process the input file
    word_counts = Counter()

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Split into words and clean them
        words = content.lower().split()

        for word in words:
            cleaned = clean_word(word)
            if cleaned and len(cleaned) > 2:  # Filter out very short words
                # Skip whitelisted words
                if cleaned not in whitelist:
                    word_counts[cleaned] += 1

        # Load existing word frequencies if output file exists
        existing_frequencies = {}
        if os.path.exists(output_file):
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    next(f)  # Skip header
                    for line in f:
                        line = line.strip()
                        if line:
                            parts = line.split(",", 2)  # Split on first two commas only
                            if len(parts) >= 2:
                                frequency = int(parts[0])
                                word = parts[1].strip('"').strip("'")
                                existing_frequencies[word] = {
                                    'frequency': frequency,
                                    'translation': parts[2].strip('"').strip("'") if len(parts) > 2 else ""
                                }
            except Exception as e:
                print(f"Warning: Could not read existing {output_file}: {e}")

        # Merge new word counts with existing frequencies
        for word, frequency in word_counts.items():
            if word in existing_frequencies:
                # Word exists, add frequencies
                existing_frequencies[word]['frequency'] += frequency
            else:
                # New word, add with empty translation
                existing_frequencies[word] = {
                    'frequency': frequency,
                    'translation': ""
                }

        # Write merged results to CSV
        with open(output_file, "w", encoding="utf-8") as f:
            # Write header
            f.write("frequency,word,translation\n")

            # Write word frequencies sorted by frequency (most common first)
            for word, data in sorted(existing_frequencies.items(),
                                   key=lambda x: x[1]['frequency'], reverse=True):
                # Escape commas and quotes in words and translations
                escaped_word = word.replace(",", ";").replace('"', '""')
                escaped_translation = data['translation'].replace(",", ";").replace('"', '""')
                f.write(f"{data['frequency']},\"{escaped_word}\",\"{escaped_translation}\"\n")

        return existing_frequencies

    except Exception as e:
        print(f"Error processing file: {e}")
        return False

def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(base_path, "words.csv")
    whitelist_file = os.path.join(base_path, "whitelist.txt")
    if len(sys.argv) > 1:
        # Clean only the specified file
        full_path = os.path.join(base_path, sys.argv[1])
        analyze_word_frequency(full_path, output_file, whitelist_file)
        os.remove(full_path)
    else:
        for filename in os.listdir(base_path):
            if filename.startswith("cleaned"):
                file_path = os.path.join(base_path, filename)
                analyze_word_frequency(file_path, output_file, whitelist_file)
                os.remove(file_path)

if __name__ == "__main__":
    main()
