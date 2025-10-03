import re
import pytesseract
import pyautogui
import time
import os
import sqlite3
import csv
from datetime import datetime
from PIL import ImageOps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

speaker_patterns = [
    r'^(User Name \d+ [A-Z]+)'
]

# Configure Tesseract path from environment
tesseract_path = os.getenv('TESSERACT_PATH')
pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Configuration from environment variables
DB_PATH = os.getenv('DB_PATH')
CSV_PATH = os.getenv('CSV_PATH')

class OCRTranslator:
    def __init__(self):
        self.recording = False
        self.interval = 1  # Default 1 second interval
        self.top_left = None
        self.bottom_right = None
        self.conn = None
        self.words_dict = {}
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self._init_database()
        self._load_csv_translations()

    def _init_database(self):
        """Initialize database connection"""
        try:
            self.conn = sqlite3.connect(DB_PATH)
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            self.conn = None

    def _load_csv_translations(self):
        """Load translations from CSV file"""
        try:
            if os.path.exists(CSV_PATH):
                with open(CSV_PATH, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        german_word = row.get('word', '').strip('"')
                        translation = row.get('translation', '').strip('"')
                        if german_word and translation:
                            # Take only the first translation (before |)
                            first_translation = translation.split('|')[0].strip()
                            self.words_dict[german_word.lower()] = first_translation
        except Exception as e:
            print(f"Error loading CSV translations: {e}")

    def get_mouse_position(self, corner_name):
        """Get mouse coordinates for specified corner"""
        print(f"Please move your mouse to the {corner_name} corner of the area you want to capture.")
        print("Press Enter when ready...")
        input()

        x, y = pyautogui.position()
        print(f"Captured {corner_name} corner coordinates: ({x}, {y})")
        return x, y

    def set_capture_area(self):
        """Set the capture area by getting corner coordinates"""
        print("\n=== Setting up capture area ===")

        # Get top-left corner
        self.top_left = self.get_mouse_position("top-left")

        # Get bottom-right corner
        self.bottom_right = self.get_mouse_position("bottom-right")

        print(f"\nCapture area set: ({self.top_left[0]}, {self.top_left[1]}) to ({self.bottom_right[0]}, {self.bottom_right[1]})")

    def set_interval(self):
        """Set the capture interval"""
        try:
            interval = float(input("Enter capture interval in seconds (default 1): "))
            if interval > 0:
                self.interval = interval
            else:
                print("Interval must be greater than 0. Using default 1 second.")
                self.interval = 1
        except ValueError:
            print("Invalid input. Using default 1 second interval.")
            self.interval = 1

    def capture_screen_area(self):
        """Capture the specified screen area"""
        if not self.top_left or not self.bottom_right:
            return None

        # Calculate width and height
        width = self.bottom_right[0] - self.top_left[0]
        height = self.bottom_right[1] - self.top_left[1]

        if width <= 0 or height <= 0:
            return None

        # Capture the screen area
        screenshot = pyautogui.screenshot(region=(self.top_left[0], self.top_left[1], width, height))
        return screenshot

    def extract_text_from_image(self, image):
        """Extract text from image using OCR"""
        try:
            # Convert to grayscale and enhance contrast
            gray_image = ImageOps.grayscale(image)

            # Try different PSM modes for better accuracy
            configs = [
                r'--oem 3 --psm 3'
            ]

            for config in configs:
                text = pytesseract.image_to_string(gray_image, lang='deu+eng', config=config)
                if text.strip():
                    return text.strip()

            return ""
        except Exception:
            return ""

    def translate_text(self, german_text):
        """Translate German text to English"""
        if not german_text or not german_text.strip():
            return ""

        translated_parts = []

        # Split by common delimiters and translate word by word
        words = german_text.split()

        for word in words:
            # Clean the word (remove punctuation for translation lookup)
            clean_word = word.strip('.,!?;:"()[]{}').lower()

            translated_word = None

            # Try database first
            if self.conn:
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("""
                        SELECT trans_list FROM translation
                        WHERE is_good = 1 AND lower(written_rep) = ?
                        ORDER BY score DESC LIMIT 1
                    """, (clean_word,))
                    result = cursor.fetchone()
                    if result:
                        trans_list = result[0]
                        # Take only the first translation (before |)
                        translated_word = trans_list.split('|')[0].strip()
                except sqlite3.Error:
                    pass

            # If not found in database, try CSV
            if not translated_word:
                translated_word = self.words_dict.get(clean_word)

            # If still no translation found, use the original word
            if not translated_word:
                translated_word = word
            
            # print(word, '->', translated_word)

            translated_parts.append(translated_word)

        return ' '.join(translated_parts)

    def _process_speaker_sentences(self, speaker_name, text_parts):
        """Process accumulated text for a speaker and print complete sentences"""
        # Join all text parts for this speaker
        full_text = ' '.join(text_parts)

        # Split into sentences based on punctuation
        sentences = re.split(r'([.!?]+)', full_text)

        # Process sentences in pairs (sentence + punctuation)
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i].strip()
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ''

            # Only process if we have a sentence with punctuation
            if sentence and punctuation.strip() in ['.', '?', '!']:
                # Translate the sentence
                translated_sentence = self.translate_text(sentence)

                # Capitalize first character and add original punctuation
                if translated_sentence.strip():
                    capitalized_sentence = translated_sentence.strip()
                    capitalized_sentence = capitalized_sentence[0].upper() + capitalized_sentence[1:] + punctuation.strip()

                    print(f"\n\n{speaker_name}")
                    print(f"{capitalized_sentence}")

    def record_and_translate(self):
        """Main recording and translation function"""
        print(f"\n=== Starting OCR translation (interval: {self.interval}s) ===")
        print("Press Ctrl+C to stop recording...")

        self.recording = True

        try:
            while self.recording:
                # Capture screen area
                screenshot = self.capture_screen_area()
                if screenshot:
                    # Extract text
                    german_text = self.extract_text_from_image(screenshot)

                    if german_text:
                        # Process the entire text to find complete sentences by speaker
                        current_speaker = None
                        current_text = []

                        # Split into lines and process each line
                        lines = german_text.splitlines()

                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue

                            # Check if this line contains a speaker name
                            speaker_name = None
                            for pattern in speaker_patterns:
                                match = re.search(pattern, line)
                                if match:
                                    speaker_name = match.group(1)
                                    break

                            if speaker_name:
                                # Process previous speaker's text if exists
                                if current_speaker and current_text:
                                    self._process_speaker_sentences(current_speaker, current_text)

                                # Start new speaker
                                current_speaker = speaker_name
                                current_text = [line.replace(speaker_name, '').strip()]
                            elif current_speaker:
                                # Continue current speaker's text
                                current_text.append(line)

                        # Process the last speaker's text
                        if current_speaker and current_text:
                            self._process_speaker_sentences(current_speaker, current_text)

                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\nRecording stopped by user.")
        finally:
            self.recording = False

    def run(self):
        """Main application loop"""
        # Setup phase
        self.set_capture_area()
        self.set_interval()

        # Recording and translation phase
        self.record_and_translate()

    def cleanup(self):
        """Cleanup resources"""
        if self.conn:
            self.conn.close()

def main():
    translator = OCRTranslator()
    try:
        translator.run()
    finally:
        translator.cleanup()
 
if __name__ == "__main__":
    main()
