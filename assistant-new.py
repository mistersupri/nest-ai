import math
import time
import wave
import speech_recognition as sr
import sounddevice as sd
import numpy as np
import threading
import queue

CHUNK = 1024  # The number of frames per buffer
FORMAT = 'int16'  # The audio format (16-bit integer)
CHANNELS = 1  # Mono audio channel
RATE = 44100  # Sampling rate (samples per second)
THRESHOLD = 100  # Adjust this threshold to control sensitivity
# Time in seconds to wait for silence before stopping recording
SILENCE_HOTWORD_INTERVAL = 0.5
# Time in seconds to wait for silence before stopping recording
SILENCE_EVAL_INTERVAL = 2

HOTWORD = "bro"
USER_VOICE_FILENAME = "recorded_audio.wav"
LANGUAGE = "id-ID"

is_eval_mode = False
audio_queue = queue.Queue()

def calculate_volume(data):
    rms = math.sqrt(sum([x ** 2 for x in data]) / len(data))
    return rms

def save_audio(frames, filename):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 2 bytes for 'int16' format
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

def transcribe_audio_to_text(filename, lang=LANGUAGE):
    r = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio = r.record(source)
    try:
        words = r.recognize_google(audio, language=lang).lower()
        print(words)
        return words
    except sr.UnknownValueError:
        print("Could not understand audio")
        return ""

def audio_callback(indata, frames, timedata, status):
    if status:
        print(status)
    audio_queue.put(indata.copy())

def process_audio():
    silence_timer = None
    is_recording = False
    frames_buffer = []
    speak_frames = []

    global is_eval_mode

    while True:
        if not audio_queue.empty():
            indata = audio_queue.get()
            volume_norm = calculate_volume(indata[:, 0])

            if volume_norm > THRESHOLD:
                if not is_recording:
                    print("Listening...")
                    is_recording = True
                if silence_timer:
                    silence_timer = None
                speak_frames.append(indata)
                frames_buffer.append(indata)
            else:
                if is_recording:
                    frames_buffer.append(indata)
                if is_recording and not silence_timer:
                    silence_timer = time.time()

                if (not is_eval_mode and silence_timer and time.time() - silence_timer > SILENCE_HOTWORD_INTERVAL) or (is_eval_mode and silence_timer and time.time() - silence_timer > SILENCE_EVAL_INTERVAL):
                    if len(speak_frames) > 0:
                        print("Evaluating...")
                        save_audio([frame.tobytes() for frame in frames_buffer], USER_VOICE_FILENAME)
                        text = transcribe_audio_to_text(USER_VOICE_FILENAME)
                        if (is_eval_mode and text != ""):
                            print("Command: " + text)
                            result = evaluate_command(text)
                            is_eval_mode = result
                        elif (HOTWORD in text):
                            answer_text = "Ya, Ada apa?"
                            print(answer_text)
                            is_eval_mode = True
                        is_recording = False
                        frames_buffer = []
                        speak_frames = []



def main():
    global is_eval_mode
    is_eval_mode = False

    print("Starting...")

    processing_thread = threading.Thread(target=process_audio, daemon=True)
    processing_thread.start()

    try:
        with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype=FORMAT, callback=audio_callback, blocksize=CHUNK):
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopped.")

if __name__ == "__main__":
    main()