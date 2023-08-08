import pyaudio
import math
import time
import wave
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import pyautogui
import openai
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, LocalAgent
from transformers import pipeline
import elevenlabs
import os
from dotenv import load_dotenv
import requests
import json
# from multiprocessing import Process, Pipe

load_dotenv()

elevenlabs.set_api_key(os.getenv("ELEVEN_API_KEY"))
openai.api_key = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOLGE_MACHINE_ID = os.getenv("GOOLGE_MACHINE_ID")

CHUNK = 1024  # The number of frames per buffer
FORMAT = pyaudio.paInt16  # The audio format (16-bit integer)
CHANNELS = 1  # Mono audio channel
RATE = 44100  # Sampling rate (samples per second)
THRESHOLD = 500  # Adjust this threshold to control sensitivity
# Time in seconds to wait for silence before stopping recording
SILENCE_HOTWORD_INTERVAL = 1
# Time in seconds to wait for silence before stopping recording
SILENCE_EVAL_INTERVAL = 3

HOTWORD = "joni"
AGENT_VOICE_FILENAME = "output.mp3"
USER_VOICE_FILENAME = "recorded_audio.wav"
LANGUAGE = "id-ID"

is_eval_mode = False


MESSAGES_TEMPLATE = {
    "basic": [
        {
            "role": "assistant",
            "content": """
            I want you to act as a response generator.
            I will provide you with question or statements,
            Your task is to generate response based on below array of objects.
            [
                {
                    "name": ["email"],
                    "type": "ALL_EMAILS"
                },
                {
                    "name": ["email", "terakhir"],
                    "type": "LATEST_EMAIL"
                },
                {   "name": ["panggilan"],
                    "type": "ALL_CALLS"
                }
            ]
            Do not include any explanations or additional information in your response, simply provide the generated response.
            The key "name" is the words that related to the question or statement and the key "type" should be the response.
            For example, if I ask you about all my emails, your response should be "ALL_EMAILS".
            If I ask you about my latest emails, your response should be "LATEST_EMAILS".

            Beside that, you will act as normal personal assistant.
            If you can not answer the question because you don't have data specific to the date,
            your response should be "ASK_GOOGLE".
            For example, if I ask you about how much the price of GPU today? your response should be "ASK_GOOGLE"
            """
        },
    ],
    "write": [
        {
            "role": "assistant",
            "content": """
            Kamu akan mengetikkan sesuatu pada komputer user. 
            Jadi, pastikan jawaban kamu sangat singkat dan tidak perlu penjelasan apa pun.
            Misal, user ingin kamu menuliskan topi dalam bahasa inggris,
            maka kamu akan menjawab 'hat' tanpa ada tambahan jawaban lain.
            """
        },
    ],
    # "google_query": [
    #     {
    #         "role": "assistant",
    #         "content": """
    #         I want you to act as a advanced google query interpreter.
    #         I will give you question or statement and you will be able to generate query for google search from that question.
    #         Do not include any explanations or additional information in your response, simply provide the generated response.
    #         """
    #     }
    # ],
}


def query(url, method="GET", payload=None, headers=None):
    if (method == "POST"):
        response = requests.request(method, url, headers=headers, json=payload)
        return json.loads(response.content.decode("utf-8"))
    response = requests.request(method, url, headers=headers, params=payload)
    return json.loads(response.content.decode("utf-8"))


def translate(text, language=LANGUAGE):
    if (language == "id-ID"):
        return text
    words = {
        "en-US": {
            "terima kasih": "thank you",
            "tulis": "write"
        }
    }
    return words[language][text]


def type_text(text, interval=0.1):
    time.sleep(5)  # Beri waktu 5 detik untuk membuka program pengetikan
    pyautogui.write(text, interval=interval)


def text_to_audio(text, audio_filename, lang=LANGUAGE[:2]):
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(audio_filename)


def play_audio(audio_filename):
    audio = AudioSegment.from_mp3(audio_filename)
    play(audio)


def play_audio_from_text_google(text):
    text_to_audio(text, AGENT_VOICE_FILENAME)
    play_audio(AGENT_VOICE_FILENAME)


def play_audio_from_text(text):
    audio = elevenlabs.generate(
        text=text,
        voice="Bella",
        model='eleven_multilingual_v1'
    )
    elevenlabs.play(audio)


# checkpoint = "tiiuae/falcon-7b"
# model = AutoModelForCausalLM.from_pretrained(
#     checkpoint, device_map="auto", torch_dtype=torch.bfloat16, trust_remote_code=True)
# tokenizer = AutoTokenizer.from_pretrained(checkpoint)


# def ask_llm(text):
#     pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
#     generated_text = pipe(text, max_length=50, do_sample=False,
#                           no_repeat_ngram_size=2)[0]
#     return generated_text['generated_text']


def ask_gpt(text, override=False, template="basic"):
    messages = MESSAGES_TEMPLATE[template] + [{
        "role": "user",
        "content": text
    }]
    if (override is True):
        messages = text
    gpt_mode = "gpt-3.5-turbo"
    response = openai.ChatCompletion.create(
        model=gpt_mode,
        messages=messages,
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response['choices'][0]['message']['content']


def evaluate_command(text):
    if (translate("terima kasih") in text.lower() or translate("terima kasih", "en-US") in text.lower()):
        return False

    if (translate("tulis") in text or translate("tulis", "en-US") in text):
        answer = ask_gpt(text, "write")
        print(answer)
        type_text(answer)
        # play_audio_from_text(answer)
        play_audio_from_text_google(answer)
    else:
        answer = ask_gpt(text)
        # if ("ASK_GOOGLE" in answer):
        #     answer = ask_gpt(text, "google_query")
        #     print(answer)
        #     data = query(
        #         f"https://www.googleapis.com/customsearch/v1", payload={
        #             "key": GOOGLE_API_KEY,
        #             "cx": GOOLGE_MACHINE_ID,
        #             "q": answer
        #         })
        #     answer = ask_gpt(text=[
        #         {
        #             "role": "assistant",
        #             "content": f"""
        #                 I want you to act as a advanced google response interpreter.
        #                 I will give you response as json object,
        #                 you will be able to summary the best answer you get from the response,
        #                 and you will be able to answer this question ("{answer}") according to the summary.
        #                 Do not include any explanations or additional information in your response, simply provide the generated response.
        #                 """
        #         },
        #         {
        #             "role": "user",
        #             "content": json.dumps(data["items"][:2])
        #         }
        #     ], override=True)
        print(answer)
        # play_audio_from_text(answer)
        # play_audio_from_text_google(answer)
        if (translate("terima kasih") in answer.lower() or translate("terima kasih", "en-US") in answer.lower()):
            return False
    return True


def calculate_volume(data):
    # Calculate the root mean square (RMS) of the audio frames to measure volume
    rms = math.sqrt(sum([x ** 2 for x in data]) / len(data))
    return rms


def save_audio(frames, filename):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pyaudio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))


def transcribe_audio_to_text(filename, lang=LANGUAGE):
    r = sr.Recognizer()
    with sr.WavFile(filename) as source:
        # extract audio data from the file
        audio = r.record(source)

    try:
        # recognize speech using Google Speech Recognition
        words = r.recognize_google(audio, language=lang).lower()
        print("Transcription: " + words)
        return words
    except:
        # speech is unintelligible
        print("Could not understand audio")
        return ""


def main():
    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    print("Starting...")
    is_recording = False
    silence_timer = None
    speak_frames = []
    frames = []
    is_eval_mode = False

    try:
        while True:
            data = stream.read(CHUNK)
            volume = calculate_volume([int.from_bytes(
                data[i:i+2], byteorder='little', signed=True) for i in range(0, len(data), 2)])
            # print("." * round(volume / 40))
            if volume > THRESHOLD:
                if not is_recording:
                    print("Listening...")
                    is_recording = True
                if silence_timer:
                    silence_timer = None

                # print(f"Volume: {volume}")
                speak_frames.append(data)
                frames.append(data)
            else:
                if is_recording:
                    # print(f"Volume: {volume}")
                    frames.append(data)
                if is_recording and not silence_timer:
                    silence_timer = time.time()

                if (not is_eval_mode and silence_timer and time.time() - silence_timer > SILENCE_HOTWORD_INTERVAL) or (is_eval_mode and silence_timer and time.time() - silence_timer > SILENCE_EVAL_INTERVAL):
                    if len(speak_frames) > 0:
                        print("Evaluating...")
                        save_audio(frames, USER_VOICE_FILENAME)
                        text = transcribe_audio_to_text(USER_VOICE_FILENAME)
                        if (is_eval_mode and text != ""):
                            print("Command: " + text)
                            result = evaluate_command(text)
                            is_eval_mode = result
                        elif (HOTWORD in text):
                            answer_text = "Ya, Ada apa?"
                            # play_audio_from_text(answer_text)
                            play_audio_from_text_google(answer_text)
                            print(answer_text)
                            is_eval_mode = True
                        is_recording = False
                        frames = []
                        speak_frames = []
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        if (os.path.exists(AGENT_VOICE_FILENAME)):
            os.remove(AGENT_VOICE_FILENAME)
        if (os.path.exists(USER_VOICE_FILENAME)):
            os.remove(USER_VOICE_FILENAME)


if __name__ == "__main__":
    main()
