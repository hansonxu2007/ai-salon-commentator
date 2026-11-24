import os
import subprocess
import wave
from pathlib import Path
from fastapi import HTTPException

def executable():
    configured = os.getenv('FFMPEG_PATH')
    if configured:
        return configured
    import shutil
    found = shutil.which('ffmpeg')
    if found:
        return found
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def split_audio(source: Path, folder: Path):
    normalized = folder / 'normalized.wav'
    try:
        result = subprocess.run([executable(), '-nostdin', '-y', '-v', 'error', '-i', str(source), '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(normalized)], capture_output=True, timeout=600)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HTTPException(500, 'FFmpeg could not run. Check FFMPEG_PATH and retry.') from exc
    if result.returncode:
        raise HTTPException(422, 'Cannot decode this recording. Check microphone input and try recording again.')
    chunks = []
    with wave.open(str(normalized), 'rb') as audio:
        while frames := audio.readframes(16000 * 60):
            path = folder / f'chunk-{len(chunks):05}.wav'
            with wave.open(str(path), 'wb') as out:
                out.setparams(audio.getparams())
                out.writeframes(frames)
            chunks.append(path)
    if not chunks:
        raise HTTPException(422, 'The recording is empty. Please record again.')
    return chunks
