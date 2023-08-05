import speech_recognition as sr
import os
import sys
from gtts import gTTS
from pydub.playback import play
from pydub import AudioSegment
import time
import pyautogui
from record import record

def type_text(text, interval=0.1):
    time.sleep(5)  # Beri waktu 5 detik untuk membuka program pengetikan
    pyautogui.write(text, interval=interval)

HOTWORD = "google"

def text_to_audio(text, lang='en'):
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save("output.mp3")

def play_audio(audio_file):
    audio = AudioSegment.from_mp3(audio_file)
    play(audio)

def listen_google(recognizer, microphone, max_silence):
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source, phrase_time_limit=max_silence)

    try:
        spoken_text = recognizer.recognize_google(audio).lower()
        print("You said:", spoken_text)
        return spoken_text
    except Exception as e:
        print(e)
        print("Voice not recognized.")  
        return ""
    # except sr.UnknownValueError: # no speech detected
    #     print("Speech not recognized.")
    #     return ""
    # except sr.RequestError as e:
    #     print("Error accessing Google Speech Recognition service; {0}".format(e))
    #     return ""

def main():
    # devnull = os.open(os.devnull, os.O_WRONLY)
    # sys.stderr.flush()
    # os.dup2(devnull, 2)
    # os.close(devnull)
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    while True:
        hotword_detected = False
        count = 0
        while not hotword_detected:
            print("Listening for hotword..." + "(" + str(count) + ")")
            spoken_text = listen_google(recognizer, microphone, 1)
            if HOTWORD in spoken_text:
                hotword_detected = True
            else:
                count += 1

        # text_to_audio("Hello, What can I help you?")
        # play_audio("output.mp3")
        print("Hotword detected. Start listening for a command...")
        time.sleep(2)
        record()
        # command = listen_google(recognizer, microphone, 5)
        # print(command)
        # if "write" in command:
        #     type_text("test 123 halo123")
        # elif command:
        #     print("Processing command:", command)

if __name__ == "__main__":
    main()
