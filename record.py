import pyaudio
import math
import time
import wave

CHUNK = 1024  # The number of frames per buffer
FORMAT = pyaudio.paInt16  # The audio format (16-bit integer)
CHANNELS = 1  # Mono audio channel
RATE = 44100  # Sampling rate (samples per second)
THRESHOLD = 500  # Adjust this threshold to control sensitivity
SILENCE_INTERVAL = 2  # Time in seconds to wait for silence before stopping recording

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

def record():
    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    print("Recording...")
    is_recording = False
    silence_timer = None
    frames = []

    try:
        while True:
            data = stream.read(CHUNK)
            volume = calculate_volume([int.from_bytes(data[i:i+2], byteorder='little', signed=True) for i in range(0, len(data), 2)])

            if volume > THRESHOLD:
                if not is_recording:
                    print("Recording started.")
                    is_recording = True
                if silence_timer:
                    silence_timer = None

                print(f"Volume: {volume}")
                frames.append(data)
            else:
                if is_recording:
                    print(f"Volume: {volume}")
                    frames.append(data)
                if is_recording and not silence_timer:
                    silence_timer = time.time()

                if silence_timer and time.time() - silence_timer > SILENCE_INTERVAL:
                    print("Silence detected. Recording stopped.")
                    break

    except KeyboardInterrupt:
        print("Recording stopped.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    if frames:
        filename = "recorded_audio.wav"
        save_audio(frames, filename)
        print(f"Recording saved to {filename}.")
