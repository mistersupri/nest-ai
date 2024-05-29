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
EVAL_INTERVAL = 0.5  # Evaluation interval in seconds

LANGUAGE = "id-ID"

audio_queue = queue.Queue()

def calculate_volume(data):
    rms = math.sqrt(sum([x ** 2 for x in data]) / len(data))
    return rms

def transcribe_audio(audio_data, lang=LANGUAGE):
    r = sr.Recognizer()
    audio = sr.AudioData(audio_data, RATE, 2)
    try:
        words = r.recognize_google(audio, language=lang).lower()
        print("Transcription: " + words)
        return words
    except sr.UnknownValueError:
        print("Could not understand audio")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
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
                if is_recording and silence_timer and time.time() - silence_timer > EVAL_INTERVAL:
                    print(len(speak_frames))
                    if len(speak_frames) > 0:
                        print("Evaluating...")
                        audio_data = np.concatenate(speak_frames, axis=0).tobytes()
                        print(audio_data, speak_frames)
                        transcribe_audio(audio_data)
                        is_recording = False
                        frames_buffer = []
                        speak_frames = []

def main():
    print("Starting...")

    audio_thread = threading.Thread(target=process_audio, daemon=True)
    audio_thread.start()

    try:
        with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype=FORMAT, callback=audio_callback, blocksize=CHUNK):
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopped.")

if __name__ == "__main__":
    main()
