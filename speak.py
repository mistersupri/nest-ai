import elevenlabs
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import os
from dotenv import load_dotenv

elevenlabs.set_api_key(os.getenv("ELEVEN_API_KEY"))

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