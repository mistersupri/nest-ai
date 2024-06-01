from termcolor import colored
from PIL import Image
from llama_api import image_answer_question
import pytesseract
import pyautogui

def take_screenshot():
    print(colored('system: Taking screenshot...', "green"))
    """Takes a screenshot of the screen."""
    screenshot = pyautogui.screenshot()
    screenshot_path = "screenshot.png"
    screenshot.save(screenshot_path)
    return screenshot_path

def analyze_screenshot(question, screenshot_path):
    print(colored('system: Analyzing screenshot...', "green"))
    """Analyzes the screenshot based on the question."""
    # Here, you could integrate image analysis using tools like OpenCV, PIL, or Tesseract.
    # For simplicity, we'll assume the screenshot contains text and use OCR.
    image = Image.open(screenshot_path)
    image_string = pytesseract.image_to_string(image)
    response = image_answer_question(question, image_string)
    return response