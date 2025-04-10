import openai
import tempfile
from pydub import AudioSegment
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def transcribe_audio(audio_bytes):
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp:
        temp.write(audio_bytes)
        temp.flush()
        audio = AudioSegment.from_file(temp.name)
        wav_path = temp.name.replace(".ogg", ".wav")
        audio.export(wav_path, format="wav")

    with open(wav_path, "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)
    return transcript['text']

def ask_gpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Sei un assistente esperto di test del DNA e nutrigenetica."},
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content']