import os
import math
import time
import wave
import speech_recognition as sr
import sounddevice as sd
from termcolor import colored
import numpy as np
import threading
import queue
from command_evaluation import evaluate_command

CHUNK = 1024  # The number of frames per buffer
FORMAT = 'int16'  # The audio format (16-bit integer)
CHANNELS = 1  # Mono audio channel
RATE = 44100  # Sampling rate (samples per second)
THRESHOLD = 200  # Adjust this threshold to control sensitivity
# Time in seconds to wait for silence before stopping recording
SILENCE_HOTWORD_INTERVAL = 0.5
# Time in seconds to wait for silence before stopping recording
SILENCE_EVAL_INTERVAL = 1

HOTWORD = "jarvis"
USER_VOICE_FILENAME = "user.wav"
LANGUAGE = "id-ID"

class AudioStream:
    def __init__(self, callback=None):
        self.is_eval_mode = False
        self.silence_timer = None
        self.is_recording = False
        self.frames_buffer = []
        self.speak_frames = []
        self.audio_queue = queue.Queue()
        self.callback = callback

    def calculate_volume(self, data):
        rms = math.sqrt(np.mean(np.square(data.astype(np.float64))))
        return rms

    def save_audio(self, frames, filename):
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # 2 bytes for 'int16' format
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))

    def transcribe_audio(self, filename, lang=LANGUAGE):
        r = sr.Recognizer()
        with sr.AudioFile(filename) as source:
            audio = r.record(source)
        try:
            words = r.recognize_google(audio, language=lang).lower()
            print("user: " + words)
            return words
        except sr.UnknownValueError:
            print("Could not understand audio")
            return ""

    def audio_callback(self, indata, frames, timedata, status):
        if status:
            print(status)
        self.audio_queue.put(indata.copy())

    def process_audio(self):
        while True:
            if not self.audio_queue.empty():
                indata = self.audio_queue.get()
                volume_norm = self.calculate_volume(indata[:, 0])

                if volume_norm > THRESHOLD:
                    if not self.is_recording:
                        print(colored('system: Listening...', "green"))
                        self.is_recording = True
                    if self.silence_timer:
                        self.silence_timer = None
                    self.speak_frames.append(indata)
                    self.frames_buffer.append(indata)
                else:
                    if self.is_recording:
                        self.frames_buffer.append(indata)
                    if self.is_recording and not self.silence_timer:
                        self.silence_timer = time.time()

                    if (self.is_recording and not self.is_eval_mode and self.silence_timer and time.time() - self.silence_timer > SILENCE_HOTWORD_INTERVAL) or (self.is_eval_mode and self.silence_timer and time.time() - self.silence_timer > SILENCE_EVAL_INTERVAL):
                        if len(self.speak_frames) > 0:
                            print(colored('system: Transcribing...', "green"))
                            self.save_audio([frame.tobytes() for frame in self.frames_buffer], USER_VOICE_FILENAME)
                            words = self.transcribe_audio(USER_VOICE_FILENAME)
                            self.callback(words)
                            # if (self.is_eval_mode and words != ""):
                            #     result = self.callback(words)
                            #     self.is_eval_mode = result
                            # elif (HOTWORD in words):
                            #     print(colored("agent: Ya, Ada apa?", "blue"))
                            #     self.is_eval_mode = True
                            self.is_recording = False
                            self.frames_buffer = []
                            self.speak_frames = []
    def start(self):
        processing_thread = threading.Thread(target=self.process_audio, daemon=True)
        processing_thread.start()
        return sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype=FORMAT, callback=self.audio_callback, blocksize=CHUNK)
    def stop(self):
        if (os.path.exists(USER_VOICE_FILENAME)):
            os.remove(USER_VOICE_FILENAME)