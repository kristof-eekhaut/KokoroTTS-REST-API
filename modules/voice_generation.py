import soundfile as sf
import os
from io import BytesIO
import numpy as np

from kokoro import KPipeline


voices_dir = 'voices'


def generate_audio(gen_text, lang_code=None, voice_name=None, samplerate=None, speed=None):
    text = gen_text.strip()
    lang_code = lang_code or 'a'
    voice_name = voice_name or 'af_heart'
    samplerate = samplerate or 24000
    speed = speed or 1

    pipeline = KPipeline(lang_code=lang_code)
    generator = pipeline(
        text, voice=voice_name,
        speed=speed, split_pattern=r'\n+'
    )

    audios = []
    for i, (gs, ps, audio) in enumerate(generator):
        print(gs) # gs => graphemes/text
        print(ps) # ps => phonemes
        audios.append(audio)

    combined_audios = np.concatenate(audios)

    audio_buffer = BytesIO()
    sf.write(audio_buffer, combined_audios, samplerate=samplerate, format="WAV")
    audio_buffer.seek(0)  # Reset buffer position to the start

    return audio_buffer


def save_wav(audio: BytesIO, model_name: str):
    wav_file = os.path.join(voices_dir, model_name + '.wav')
    with open(wav_file, "wb") as f:
        f.write(audio.getbuffer())
    return wav_file
