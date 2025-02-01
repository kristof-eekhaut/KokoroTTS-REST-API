from flask import Flask, request, send_file, jsonify
import soundfile as sf
from io import BytesIO
import numpy as np

from kokoro import KPipeline

import gc


app = Flask(__name__)


def generate_audio(gen_text, voice_name=None):
    text = gen_text.strip()
    voice_name = voice_name or 'af_heart'

    samplerate = 24000
    lang_code = voice_name[0]
    pipeline = KPipeline(lang_code=lang_code)
    generator = pipeline(
        text, voice=voice_name,
        speed=1, split_pattern=r'\n+'
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


@app.route('/generate_audio', methods=['POST'])
def generate_audio_api():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400

    text = data['text']
    voice_name = data['voice'] if 'voice' in data else None

    audio_buffer = generate_audio(text, voice_name)

    return send_file(
        audio_buffer,
        as_attachment=True,
        download_name="generated_audio.wav",
        mimetype="audio/wav"
    )


if __name__ == '__main__':
    try:
        # Start the server
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        gc.collect()