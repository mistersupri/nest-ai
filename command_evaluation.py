from termcolor import colored
from llama_api import ask_gpt_category, answer_basic_question
from screenshot import take_screenshot, analyze_screenshot

def evaluate_command(text):
    print(colored('system: Evaluating...', "green"))
    if (ask_gpt_category(text) == "screen"):
        screenshot_path = take_screenshot()
        analysis = analyze_screenshot(text, screenshot_path)
        print(analysis)
    elif (ask_gpt_category(text) == "email"):
        print("email")
    elif (ask_gpt_category(text) == "highlight"):
        print("highlight")
    else:
        print(colored('system: Answering...', "green"))
        response = answer_basic_question(text)
        print(response)
