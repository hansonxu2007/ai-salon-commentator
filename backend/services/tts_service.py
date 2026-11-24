import wave
from fastapi import HTTPException
from .provider import client, check

def synthesize(text, voice, target):
    try:
        with client() as api, api.stream('POST', '/v1/tools/tts', json={'text':text,'voice_id':voice,'format':'wav'}) as response:
            check(response)
            with target.open('wb') as out:
                for chunk in response.iter_bytes():
                    out.write(chunk)
        # Streamed WAV often declares 0xffffffff bytes until EOF. Read in
        # bounded blocks and replace that placeholder with an actual header.
        fixed = target.with_suffix('.fixed.wav')
        try:
            with wave.open(str(target), 'rb') as audio, wave.open(str(fixed), 'wb') as out:
                out.setparams(audio.getparams())
                out.setnframes(0)
                frame_size = audio.getnchannels() * audio.getsampwidth()
                expected = audio.getnframes() * frame_size
                total = 0
                while block := audio.readframes(65536):
                    total += len(block)
                    out.writeframesraw(block)
                placeholder = 0xffffffff - frame_size < expected <= 0xffffffff
                if not total or total % frame_size or (not placeholder and total != expected):
                    raise ValueError('Incomplete WAV')
            fixed.replace(target)
        finally:
            fixed.unlink(missing_ok=True)
    except (wave.Error, EOFError, ValueError) as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(502, 'TTS returned incomplete or invalid audio. Retry synthesis.') from exc
