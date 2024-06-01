from termcolor import colored
from ollama import Client

client = Client(host='http://localhost:11434')

def answer_basic_question(question):
    model = 'llama-custom'
    prompt = question
    try:
        promise = client.generate(model=model, prompt=prompt)
        return promise['response']
    except client.ResponseError as e:
        print(colored('system: Error' + e.error, "red"))
        if e.status_code == 404:
            client.pull(model)

def ask_gpt_category(question):
    model = 'llama-custom'
    prompt = "KEEP IT SHORT AND ONLY ANSWER THIS ('screen', 'email', 'highlight', 'basic question') WITHOUT ADDITIONAL SYMBOL OR CAPITAL CASE. Termasuk apa kategori dari pertanyaan berikut? ('screen', 'email', 'highlight', 'basic question'): \"" + question +"\""
    try:
        promise = client.generate(model=model, prompt=prompt)
        return promise['response']
    except client.ResponseError as e:
        print(colored('system: Error' + e.error, "red"))
        if e.status_code == 404:
            client.pull(model)

def image_answer_question(question, image_string):
    print(colored('system: Answering...' + e.error, "green"))
    model = 'llava'
    prompt = question
    try:
        promise = client.generate(model=model, prompt=prompt, images=[image_string])
        return promise['response']
    except client.ResponseError as e:
        print(colored('system: Error' + e.error, "red"))
        if e.status_code == 404:
            client.pull(model)