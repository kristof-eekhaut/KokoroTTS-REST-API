from fastapi import BackgroundTasks, FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel
import uvicorn

from modules.voice_generation import generate_audio, voices_dir

import os

app = FastAPI()

# Add CORS middleware
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post('/set_tts_settings')
def set_tts_settings_endpoint():
    return


@app.get('/speakers')
def get_speakers():
    speakers = []
    voices = [os.path.splitext(f)[0] for f in os.listdir(voices_dir) if f.endswith('.pt')]
    voices.sort()
    for voice in voices:
        speakers.append({
            'name': voice,
            'voice_id': voice,
            'preview_url': ''
        })

    return speakers


@app.get('/tts_stream')
async def tts_stream(request: Request, text: str = Query(), speaker_wav: str = Query(), language: str = Query()):

    if not text:
        return JSONResponse({"error": "No text provided"}, 400)

    async def generator():
        audio_buffer = generate_audio(
            text,
            None,
            os.path.join(voices_dir, speaker_wav + '.pt'),
            None
        )

        # Check if the client is still connected.
        disconnected = await request.is_disconnected()
        if disconnected:
            return

        yield audio_buffer.getvalue()

    return StreamingResponse(generator(), media_type='audio/x-wav')


class GenerateAudioRequest(BaseModel):
    text: str
    speaker_wav: str
    language: str = None


@app.post("/tts_to_audio/")
async def tts_to_audio(request: GenerateAudioRequest, background_tasks: BackgroundTasks):

    if not request or not request.text:
        return JSONResponse({"error": "No text provided"}, 400)

    audio_buffer = generate_audio(
        request.text,
        None,
        os.path.join(voices_dir, request.speaker_wav + '.pt'),
        None
    )

    background_tasks.add_task(audio_buffer.close)
    headers = {'Content-Disposition': 'inline; filename="generated_audio.wav"'}
    return Response(audio_buffer.getvalue(), headers=headers, media_type='audio/wav')


if __name__ == '__main__':
    # Start the server
    uvicorn.run(app,host="0.0.0.0",port=5000)
