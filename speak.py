import elevenlabs
from elevenlabs.client import ElevenLabs
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import os
from dotenv import load_dotenv

load_dotenv()

LANGUAGE="id-ID"
AGENT_VOICE_FILENAME = "agent.mp3"

client=ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

def text_to_audio(text, audio_filename, lang=LANGUAGE[:2]):
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(audio_filename)


def play_audio(audio_filename):
    audio = AudioSegment.from_mp3(audio_filename)
    play(audio)


def play_audio_from_text_google(text):
    text_to_audio(text, AGENT_VOICE_FILENAME)
    play_audio(AGENT_VOICE_FILENAME)


def play_audio_from_text_eleven(text):
    audio = client.generate(
        text=text,
        model='eleven_turbo_v2'
    )
    elevenlabs.play(audio)