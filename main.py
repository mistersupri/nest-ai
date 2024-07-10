
import cv2
from termcolor import colored
from audio_stream import AudioStream
from webcam_stream import WebcamStream
from lang_chain_assistant import assistant

camera_stream = WebcamStream().start()

def evaluate(words):
    if (words):
        result = assistant.answer(words, camera_stream.read(encode=True))
        print(colored('agent: ' + result, "yellow"))

def main():
    print(colored('system: Starting...', "green"))
    audio_stream = AudioStream(callback=evaluate)
    try:
        with audio_stream.start():
            while True:
                cv2.imshow("webcam", camera_stream.read())
                if cv2.waitKey(1) in [27, ord("q")]:
                    break
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        camera_stream.stop()
        audio_stream.stop()

if __name__ == "__main__":
    main()