import pytesseract
import pyautogui
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Tesseract path from environment
tesseract_path = os.getenv('TESSERACT_PATH')
pytesseract.pytesseract.tesseract_cmd = tesseract_path

class OCRRecorder:
    def __init__(self):
        self.recording = False
        self.interval = 1  # Default 1 second interval
        self.top_left = None
        self.bottom_right = None
        self.session_text = []
        self.start_timestamp = None
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

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
            print("Error: Capture area not set!")
            return None

        # Calculate width and height
        width = self.bottom_right[0] - self.top_left[0]
        height = self.bottom_right[1] - self.top_left[1]

        if width <= 0 or height <= 0:
            print("Error: Invalid capture area dimensions!")
            return None

        # Capture the screen area
        screenshot = pyautogui.screenshot(region=(self.top_left[0], self.top_left[1], width, height))
        return screenshot

    def extract_text_from_image(self, image):
        """Extract text from image using OCR"""
        try:
            # Try minimal preprocessing first
            from PIL import ImageOps

            # Convert to grayscale only (minimal processing)
            gray_image = ImageOps.grayscale(image)

            # Try different PSM modes with minimal preprocessing
            text_results = []
         
            config = r'--oem 3 --psm 3'
            text = pytesseract.image_to_string(gray_image, lang='deu+eng', config=config)
            text_results.append(text)

            return text.strip()
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    def record_screen(self):
        """Main recording function"""
        print(f"\n=== Starting OCR recording (interval: {self.interval}s) ===")
        print("Press Ctrl+C to stop recording...")

        # Generate timestamp at the start of recording (use Windows-safe format)
        self.start_timestamp = datetime.now().strftime("%d.%m.%Y-%H-%M")
        print(f"Recording started at: {self.start_timestamp}")

        self.recording = True
        self.session_text = []

        try:
            while self.recording:
                # Capture screen area
                screenshot = self.capture_screen_area()
                if screenshot:
                    # Extract text
                    text = self.extract_text_from_image(screenshot)

                    if text:  # Only process non-empty text
                        print(text)
                        self.session_text.append(text)

                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\nRecording stopped by user.")
        finally:
            self.recording = False
            self.save_session()

    def save_session(self):
        """Save session data to files"""
        if not self.session_text:
            print("No text captured in this session.")
            return

        # Use the start timestamp for filenames (not current time)
        if not self.start_timestamp:
            self.start_timestamp = datetime.now().strftime("%d.%m.%Y-%H-%M")

        try:
            # Ensure .txt extension is always included
            session_filename = os.path.join(self.script_dir, f"session-{self.start_timestamp}.txt")

            # Save session text with timestamp in filename
            with open(session_filename, "w", encoding="utf-8") as f:
                for i, text in enumerate(self.session_text, 1):
                    f.write(f"{text}\n")

            print(f"\nSession data saved to:")
            print(f"  {session_filename}")

        except Exception as e:
            print(f"Error saving session data: {e}")

    def run(self):
        """Main application loop"""
        # Setup phase
        self.set_capture_area()
        self.set_interval()

        # Recording phase
        self.record_screen()

def main():
    recorder = OCRRecorder()
    recorder.run()

if __name__ == "__main__":
    main()
