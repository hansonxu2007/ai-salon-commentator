import re
import os
import shutil
import tempfile
import uuid
from pathlib import Path
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Literal
from .services.audio_service import split_audio, executable
from .services.asr_service import transcribe
from .services.commentary_service import generate
from .services.tts_service import synthesize

ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = Path(os.getenv('SALON_HOME', str(ROOT)))
load_dotenv(CONFIG_ROOT / '.env')
DATA = CONFIG_ROOT / 'backend/data'
DATA.mkdir(exist_ok=True, parents=True)
app = FastAPI(title='AI Salon Commentator')

@app.exception_handler(httpx.HTTPError)
async def provider_error(request, exc):
    return JSONResponse(status_code=502, content={'detail':'Cannot reach DeepSeek or the connection was interrupted. Check your connection and retry.'})

class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=60000)

class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    voice: Literal['stella', 'tide'] = 'stella'

def nonempty(text):
    if not text.strip():
        raise HTTPException(422, 'Please enter some text first.')
    return text.strip()

@app.get('/api/health')
def health():
    import os
    return {'status':'ok','product':'ai-salon-commentator','api_key_configured':bool(os.getenv('DEEPSEEK_API_KEY')), 'ffmpeg_available':Path(executable()).exists() or bool(shutil.which(executable()))}

@app.post('/api/transcribe')
def upload(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory(dir=DATA) as tmp:
        folder = Path(tmp)
        source = folder / 'recording.bin'
        size = 0
        with source.open('wb') as out:
            while block := file.file.read(1024 * 1024):
                size += len(block)
                if size > 200 * 1024 * 1024:
                    raise HTTPException(413, 'Recording exceeds the 200 MiB local upload limit.')
                out.write(block)
        chunks = split_audio(source, folder)
        return {'text':transcribe(chunks), 'segments':len(chunks)}

@app.post('/api/commentary')
def commentary(body: TextRequest):
    return {'text':generate(nonempty(body.text))}

@app.post('/api/synthesize')
def speech(body: SpeechRequest):
    name = uuid.uuid4().hex + '.wav'
    target = DATA / name
    try:
        synthesize(nonempty(body.text), body.voice, target)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return {'audio_url':f'/api/audio/{name}'}

@app.get('/api/audio/{name}')
def audio(name: str):
    if not re.fullmatch(r'[0-9a-f]{32}\.wav', name) or not (DATA / name).is_file():
        raise HTTPException(404, 'Audio not found. Please synthesize again.')
    return FileResponse(DATA / name, media_type='audio/wav', headers={'Cache-Control':'no-store'})

# Portable distribution serves the compiled UI from the same local origin.
STATIC = ROOT / 'frontend/dist'
if STATIC.is_dir():
    app.mount('/', StaticFiles(directory=STATIC, html=True), name='frontend')
