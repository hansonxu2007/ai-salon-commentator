from .provider import client, check
from fastapi import HTTPException

def transcribe(chunks):
    texts = []
    with client() as api:
        for chunk in chunks:
            with chunk.open('rb') as audio:
                response = api.post('/v1/tools/asr', files={'file': (chunk.name, audio, 'audio/wav')})
            check(response)
            value = response.json().get('text')
            if not isinstance(value, str):
                raise HTTPException(502, 'ASR returned an invalid transcript. Retry transcription.')
            texts.append(value.strip())
    text = '\n\n'.join(t for t in texts if t)
    if not text:
        raise HTTPException(422, 'No speech was recognized. Check microphone input or edit the transcript manually.')
    return text
