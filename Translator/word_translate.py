import csv
import sqlite3
import requests
import json
import os
import signal
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment variables
DB_PATH = os.getenv('DB_PATH')
CSV_PATH = os.getenv('CSV_PATH')
WHITELIST_PATH = os.getenv('WHITELIST_PATH')
DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')
DEEPL_API_URL = os.getenv('DEEPL_API_URL')

# SQL query to find translation in database
SQL_QUERY = """
    SELECT trans_list, score FROM translation
    WHERE is_good = 1 AND lower(written_rep) = lower(?)
    ORDER BY score DESC LIMIT 1;
"""

def get_translation_from_db(word, conn):
    """Get translation from SQLite database"""
    try:
        cursor = conn.cursor()
        cursor.execute(SQL_QUERY, (word,))
        result = cursor.fetchone()
        if result:
            trans_list, score = result
            return trans_list
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    return None

def get_translation_from_deepl(word):
    """Get translation from DeepL API"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'DeepL-Auth-Key {DEEPL_API_KEY}'
    }

    json_data = {
        "text": [word],
        "source_lang": "DE",
        "target_lang": "EN"
    }

    try:
        response = requests.post(DEEPL_API_URL, headers=headers, json=json_data)
        response.raise_for_status()

        result = response.json()
        if result and 'translations' in result and len(result['translations']) > 0:
            return result['translations'][0]['text']
    except requests.RequestException as e:
        pass
        # print(f"DeepL API error: {e}")
    return None

# Global variable to store words_data for signal handler
global_words_data = []

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully by saving progress"""
    print(f"\n\n⚠️  Interrupted by user! Saving progress...")
    if global_words_data:
        save_progress(global_words_data)
    print("✅ Progress saved. You can resume later.")
    sys.exit(0)

def save_progress(words_data):
    """Save current progress to CSV file"""
    try:
        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['frequency', 'word', 'translation'], quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(words_data)
        print("✅ Progress saved to CSV file")
    except Exception as e:
        print(f"❌ Error saving progress: {e}")

def add_to_whitelist(word):
    """Add word to whitelist.txt file"""
    try:
        with open(WHITELIST_PATH, 'a', encoding='utf-8') as file:
            file.write(f"{word}\n")
        print(f"  📝 Added '{word}' to whitelist.txt")
    except Exception as e:
        print(f"❌ Error adding to whitelist: {e}")

def filter_words_data(words_data, word_to_remove):
    """Remove word from words_data and return filtered list"""
    return [row for row in words_data if row.get('word', '').strip('"') != word_to_remove]

def translate_words():
    """Main function to translate words from CSV"""
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    try:
        # Read current CSV
        global global_words_data
        words_data = []
        if os.path.exists(CSV_PATH):
            with open(CSV_PATH, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                words_data = list(reader)

        # Store in global variable for signal handler
        global_words_data = words_data

        # Count words that need translation
        words_to_translate = []
        for row in words_data:
            if not row.get('translation', '').strip('"'):
                words_to_translate.append(row)

        total_words = len(words_to_translate)
        print(f"📊 Found {total_words} words that need translation")

        if total_words == 0:
            print("✅ All words already have translations!")
            return

        # Process each word
        processed_count = 0
        skipped_count = 0
        i = 0  # Separate index for original words_data

        while i < len(words_data):
            row = words_data[i]
            word = row.get('word', '').strip('"')

            # Skip if already has translation
            if row.get('translation', '').strip('"'):
                i += 1
                continue

            processed_count += 1
            remaining_words = total_words - skipped_count
            print(f"\n🔄 [{processed_count}/{remaining_words}] Processing word: '{word}'")

            # Try database first
            translation = get_translation_from_db(word, conn)

            # If not found in database, use DeepL
            if not translation:
                translation = get_translation_from_deepl(word)

                # If DeepL also fails, prompt user for manual translation
                if not translation:
                    user_translation = input(word).strip()
                    if user_translation:
                        translation = user_translation
                    else:
                        print(f"  ⏭️  Skipping word: '{word}'")
                        # Add to whitelist and remove from processing
                        add_to_whitelist(word)
                        # Remove this word from words_data
                        words_data.pop(i)
                        global_words_data = words_data
                        skipped_count += 1
                        continue

            # Update the row if translation found
            if translation:
                row['translation'] = translation
                print(f"  ✅ Translation: {translation}")
            else:
                print(f"  ❌ No translation found for: {word}")

            i += 1

        # Final save
        save_progress(words_data)
        print(f"\n🎉 Translation complete! Processed {processed_count} words.")

    finally:
        conn.close()

if __name__ == "__main__":
    translate_words()
