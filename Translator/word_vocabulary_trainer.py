#!/usr/bin/env python3
"""
Vocabulary Trainer Script
Reads words from words.csv, prompts user for translations,
and manages learned words in whitelist.txt and de-en.sqlite3 database
"""

import csv
import os
import random
import sys
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VocabularyTrainer:
    def __init__(self, words_file='words.csv', whitelist_file='whitelist.txt', db_file='de-en.sqlite3'):
        self.words_file = words_file
        self.whitelist_file = whitelist_file
        self.db_file = db_file
        self.words = []
        self.whitelist = set()
        self.load_data()

    def load_data(self):
        """Load words from CSV and whitelist from text file"""
        # Load words from CSV
        if os.path.exists(self.words_file):
            with open(self.words_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                self.words = list(reader)

        # Load whitelist
        if os.path.exists(self.whitelist_file):
            with open(self.whitelist_file, 'r', encoding='utf-8') as file:
                self.whitelist = {line.strip().lower() for line in file if line.strip()}

    def save_words(self):
        """Save updated words back to CSV"""
        if self.words:
            with open(self.words_file, 'w', newline='', encoding='utf-8') as file:
                if self.words:
                    writer = csv.DictWriter(file, fieldnames=['frequency', 'word', 'translation'])
                    writer.writeheader()
                    writer.writerows(self.words)

    def save_whitelist(self):
        """Save updated whitelist to text file"""
        with open(self.whitelist_file, 'w', encoding='utf-8') as file:
            for word in sorted(self.whitelist):
                file.write(f"{word}\n")

    def get_random_word(self):
        """Get a random word that hasn't been learned yet"""
        available_words = [word for word in self.words if word['word'].lower() not in self.whitelist]
        return random.choice(available_words) if available_words else None

    def check_translation(self, word, user_translation):
        """Check if user's translation is correct"""
        correct_translations = [t.strip().lower() for t in word['translation'].split('|')]
        user_translation = user_translation.strip().lower()
        return user_translation in correct_translations

    def check_translation_in_db(self, german_word, english_translation):
        """Check if translation exists in database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # Check in translation table using the same pattern as other files
            cursor.execute("""
                SELECT COUNT(*) FROM translation
                WHERE is_good = 1 AND lower(written_rep) = lower(?) AND lower(trans_list) = lower(?)
            """, (german_word, english_translation))

            count = cursor.fetchone()[0]
            conn.close()

            return count > 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def add_translation_to_db(self, german_word, english_translation):
        """Add translation to database if it doesn't exist"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # Check if it already exists before adding
            if not self.check_translation_in_db(german_word, english_translation):
                # Add to translation table using the same pattern as other files
                cursor.execute("""
                    INSERT INTO translation (written_rep, trans_list, score, is_good)
                    VALUES (?, ?, ?, ?)
                """, (german_word.lower(), english_translation.lower(), 1, 1))

                conn.commit()
                print(f"💾 Added '{german_word}' -> '{english_translation}' to database")
            else:
                print(f"💾 Translation '{german_word}' -> '{english_translation}' already exists in database")

            conn.close()
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def run_training_session(self):
        """Main training loop"""
        print("🎓 Vocabulary Trainer")
        print("=" * 50)
        print("Type 'quit' or 'exit' to end the session")
        print("Press Ctrl+C to end the session")
        print("Type 'hint' to get a hint")
        print()

        words_learned = 0
        total_words = len(self.words) - len(self.whitelist)

        while True:
            word = self.get_random_word()
            if not word:
                print("🎉 Congratulations! You've learned all available words!")
                break

            german_word = word['word']
            print(f"\n📝 Translate: '{german_word}'")
            print(f"💡 Frequency: {word['frequency']}")

            while True:
                try:
                    user_input = input("\nYour translation: ").strip()

                    if user_input.lower() in ['quit', 'exit']:
                        print(f"\n👋 Session ended. You learned {words_learned} words this session.")
                        return

                    if user_input.lower() == 'hint':
                        # Show first translation option as hint
                        first_translation = word['translation'].split('|')[0].strip()
                        print(f"💡 Hint: {first_translation}")
                        continue

                    if self.check_translation(word, user_input):
                        print("✅ Correct!")
                        # Remove from words and add to whitelist
                        self.words = [w for w in self.words if w['word'] != german_word]
                        self.whitelist.add(german_word.lower())
                        words_learned += 1

                        # Check and add translation to database
                        self.add_translation_to_db(german_word, user_input)

                        # Save progress
                        self.save_words()
                        self.save_whitelist()

                        remaining = len(self.words) - len(self.whitelist)
                        print(f"🎯 Progress: {words_learned} learned this session, {remaining} words remaining")
                        break
                    else:
                        correct_answer = word['translation']
                        print(f"❌ Incorrect. Correct translation: '{correct_answer}'")
                        break

                except KeyboardInterrupt:
                    print(f"\n\n👋 Session interrupted. You learned {words_learned} words this session.")
                    return
                except EOFError:
                    print(f"\n\n👋 Session ended. You learned {words_learned} words this session.")
                    return

def main():
    trainer = VocabularyTrainer()
    trainer.run_training_session()

if __name__ == "__main__":
    main()
