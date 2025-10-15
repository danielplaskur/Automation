import datetime
import re
import pytesseract
import pyautogui
import os
from PIL import ImageOps

pytesseract.pytesseract.tesseract_cmd = r"C:\Users\sotdb\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
speaker_patterns = [
    r'^([A-Z][a-z]+ [A-Z][a-z]+ \d+ [A-Z]+)'
]
combined_pattern = re.compile(r'|'.join(speaker_patterns), re.MULTILINE)


def extract_speaker_blocks(text):
    """Extract blocks of text grouped by speaker until the next speaker appears"""
    blocks = []
    current_speaker = None
    current_text = []

    for line in text.splitlines():
        match = combined_pattern.match(line)
        if match:
            if current_speaker and current_text:
                blocks.append((current_speaker, '\n'.join(current_text).strip()))
            current_speaker = match.group(0)
            current_text = [line]
        else:
            if current_speaker:
                current_text.append(line)

    if current_speaker and current_text:
        blocks.append((current_speaker, '\n'.join(current_text).strip()))

    return blocks


def get_mouse_position():
    """Get mouse coordinates for specified corner"""
    print("Click on top-left corner and press Enter...", end=" ")
    input()
    top_left_x, top_left_y = pyautogui.position()

    print("Click on bottom-right corner and press Enter...", end=" ")
    input()

    bottom_right_x, bottom_right_y = pyautogui.position()

    print(f"Capture area: ({top_left_x}, {top_left_y}) to ({bottom_right_x}, {bottom_right_y})")
    print("=" * 50)

    return top_left_x, top_left_y, bottom_right_x, bottom_right_y


def capture_screen_area(top_left_x: int, top_left_y: int, bottom_right_x: int, bottom_right_y: int):
    """Capture the specified screen area"""
    width = bottom_right_x - top_left_x
    height = bottom_right_y - top_left_y

    if width <= 0 or height <= 0:
        print(f"Error: Invalid capture area dimensions! Width: {width}, Height: {height}")
        return None

    try:
        screenshot = pyautogui.screenshot(region=(top_left_x, top_left_y, width, height))
        return screenshot
    except Exception as e:
        print(f"Error capturing screen area: {e}")
        return None


def extract_text_from_image(image):
    """Extract text from image using OCR"""
    try:
        gray_image = ImageOps.grayscale(image)

        config = r'--oem 3 --psm 3'
        text = pytesseract.image_to_string(gray_image, lang='deu+eng', config=config)

        return text.strip()
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""


def save_session(session_path, session):
    """Save the current session to a text file"""
    with open(session_path, "w", encoding="utf-8") as f:
        for text in session:
            f.write(text + "\n")
    print(f"Content saved to {session_path}")


def get_word_freq(whitelist_path, session):
    """Get word frequency from session texts, excluding whitelisted words"""
    with open(whitelist_path) as f:
        whitelist = set(f.read().splitlines())
    word_freq = {}
    for text in session:
        words = text.split()
        for word in words:
            if word.lower() not in whitelist:
                clean_word = word.replace('.', '').replace('?', '').replace(',', '').lower()
                if not clean_word.isdigit():
                    word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
    return word_freq


def save_word_freq(word_freq_path, word_freq):
    """Save word frequency to a text file"""
    with open(word_freq_path, "r", encoding="utf-8") as f:
        for line in f:
            count, word = line.strip().split(",", 1)
            word_freq[word] = word_freq.get(word, 0) + int(count)
    sorted_word_freq = dict(sorted(word_freq.items(), key=lambda item: item[1], reverse=True))
    with open(word_freq_path, "w", encoding="utf-8") as f:
        for word, count in sorted_word_freq.items():
                f.write(f"{count},{word}\n")


def main():
    timestamp = datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")

    base_path = os.path.dirname(os.path.abspath(__file__))
    word_freq_path = os.path.join(base_path, "word_frequency.txt")
    whitelist_path = os.path.join(base_path, "whitelist.txt")
    session_path = os.path.join(base_path, f"session-{timestamp}.txt")

    print("Starting OCR capture session...")
    print("Press Ctrl+C to stop and save the session.")

    try:
        top_left_x, top_left_y, bottom_right_x, bottom_right_y = get_mouse_position()
    except KeyboardInterrupt:
        print("\nSetup cancelled by user.")
        return

    session = set()
    try:
        while True:
            image = capture_screen_area(top_left_x, top_left_y, bottom_right_x, bottom_right_y)
            if image is None:
                continue
            text = extract_text_from_image(image).replace('|', 'I')
            sentences = extract_speaker_blocks(text)
            for speaker_name, block_text in sentences:
                remaining_text = block_text.replace(speaker_name, '').strip()
                if remaining_text:
                    capitalized_text = remaining_text[0].upper() + remaining_text[1:] if len(remaining_text) > 1 else remaining_text.upper()
                else:
                    capitalized_text = ""
                session_text = f"\n{speaker_name}\n{capitalized_text.replace('\n', ' ')}"
                if "(Unverified)" not in session_text:
                    if session_text not in session:
                        print(session_text)
                    session.add(session_text)
    except KeyboardInterrupt:
        print(f"\nSaving {len(session)} unique session entries...")

        try:
            save_session(session_path, session)
            word_freq = get_word_freq(whitelist_path, session)
            save_word_freq(word_freq_path, word_freq)
            print("Session saved successfully!")
        except Exception as e:
            print(f"Error saving session: {e}")
        

if __name__ == "__main__":
    main()
