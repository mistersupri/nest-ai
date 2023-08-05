import pyaudio
import math
import time
import wave
import pyttsx3
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import pyautogui
import openai

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

is_eval_mode = False

openai.api_key_path = "./.api_key"


def type_text(text, interval=0.1):
    time.sleep(5)  # Beri waktu 5 detik untuk membuka program pengetikan
    pyautogui.write(text, interval=interval)


def text_to_audio(text, audio_filename, lang='id'):
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(audio_filename)


def play_audio(audio_filename):
    audio = AudioSegment.from_mp3(audio_filename)
    play(audio)


def evaluate_command(text, temperature=0):
    gpt_mode = "gpt-3.5-turbo"
    output_filename = "output.mp3"
    if ("tulis" in text):
        response = openai.ChatCompletion.create(
            model=gpt_mode,
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": "Kamu akan mengetikkan sesuatu pada komputer user. Jadi, pastikan jawaban kamu sangat singkat dan tidak perlu penjelasan apa pun. Misal, user ingin kamu menuliskan topi dalam bahasa inggris, maka kamu akan menjawab 'hat' tanpa ada tambahan jawaban lain."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )
        answer = response['choices'][0]['message']['content']
        print(answer)
        type_text(answer)
        text_to_audio(answer, output_filename)
        play_audio(output_filename)
    else:
        response = openai.ChatCompletion.create(
            model=gpt_mode,
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": "Kamu adalah seorang yang sangat pintar dari semua pelajaran. Jawablah semua pertanyaan dari user. Tidak perlu menjelaskan secara spesifik dan jawab secukupnya. Tanyakan apakah user ingin bertanya lagi. Jika user tidak ingin bertanya lagi, jangan lupa ucapkan 'terima kasih ya!'"
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )
        answer = response['choices'][0]['message']['content']
        print(answer)
        text_to_audio(answer, output_filename)
        play_audio(output_filename)
        if ("terima kasih" in answer.lower()):
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


# def transcribe_audio_to_text_using_gpt(audio_file_name, temperature=0):
#     system_prompt = "Kamu adalah Joni, seorang editor untuk perusahaan ZyntriQix. Tugas kamu adalah untuk memperbaiki kesalahan kata yang diajukan oleh user. Tidak perlu menjawab pertanyaan dari user dan tidak perlu mengulangi kata yang disebutkan oleh user. Pastikan nama dari produk-produk berikut ini sesuai: ZyntriQix, Digique Plus, CynapseFive, VortiQore V8, EchoNix Array, OrbitalLink Seven, DigiFractal Matrix, PULSE, RAPT, B.R.I.C.K., Q.U.A.R.T.Z., F.L.I.N.T. Hanya tambah tanda baca yang perlu seperti titik, koma, kapital, dan jika terdapat konteks tambahan."
#     try:
#         audio_file = open(audio_file_name, "rb")
#         transcript = openai.Audio.transcribe("whisper-1", audio_file)
#         response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo",
#             temperature=temperature,
#             messages=[
#                 {
#                     "role": "system",
#                     "content": system_prompt
#                 },
#                 {
#                     "role": "user",
#                     "content": transcript["text"]
#                 }
#             ]
#         )
#         transcript = response['choices'][0]['message']['content']
#         print("Transription: ", transcript)
#         return transcript.lower()
#     except Exception as e:
#         print(e)
#         print("Could not understand audio")
#         return ""


def transcribe_audio_to_text(filename):
    r = sr.Recognizer()
    # use "test.wav" as the audio source
    with sr.WavFile(filename) as source:
        # extract audio data from the file
        audio = r.record(source)

    try:
        words = r.recognize_google(audio, language="id-ID").lower()
        # recognize speech using Google Speech Recognition
        print("Transcription: " + words)
        return words
    except:                                 # speech is unintelligible
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
    # eval_mode = "unknown"

    try:
        while True:
            data = stream.read(CHUNK)
            volume = calculate_volume([int.from_bytes(
                data[i:i+2], byteorder='little', signed=True) for i in range(0, len(data), 2)])

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
                        filename = "recorded_audio.wav"
                        save_audio(frames, filename)
                        text = transcribe_audio_to_text(filename)
                        if (is_eval_mode):
                            print("Command: " + text)
                            result = evaluate_command(text)
                            is_eval_mode = result
                        elif (HOTWORD in text):
                            output_filename = "output.mp3"
                            answer_text = "Iya, ada apa?"
                            text_to_audio(answer_text, output_filename)
                            play_audio(output_filename)
                            print(answer_text)
                            is_eval_mode = True
                        frames = []
                        speak_frames = []
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    main()
