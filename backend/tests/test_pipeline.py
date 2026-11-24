import io
import os
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.audio_service import split_audio
from backend.services.asr_service import transcribe
from backend.services.commentary_service import generate
from backend.services.tts_service import synthesize

def wav_bytes(seconds=1):
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(16000)
        out.writeframes(b'\x00\x00' * (16000 * seconds))
    return buffer.getvalue()

class PipelineTests(unittest.TestCase):
    def test_long_recording_keeps_tail(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'source.wav'
            source.write_bytes(wav_bytes(125))
            parts = split_audio(source, root)
            counts = []
            for part in parts:
                with wave.open(str(part), 'rb') as audio:
                    counts.append(audio.getnframes())
                    self.assertEqual((audio.getframerate(), audio.getnchannels(), audio.getsampwidth()), (16000, 1, 2))
                self.assertLess(part.stat().st_size, 8 * 1024 * 1024)
            self.assertEqual(counts, [960000, 960000, 80000])

    def test_provider_contract_and_order(self):
        import json
        calls = []
        def handler(request):
            calls.append(request)
            if request.url.path.endswith('/asr'):
                self.assertIn(b'name="file"', request.read())
                return httpx.Response(200, json={'text':f'Part {len(calls)}'})
            body = json.loads(request.read())
            if request.url.path.endswith('/completions'):
                self.assertEqual(body['model'], 'deepseek-flash')
                self.assertEqual(body['thinking'], {'type':'disabled'})
                self.assertEqual(body['messages'][1]['content'], 'edited transcript')
                return httpx.Response(200, json={'choices':[{'message':{'content':'A thoughtful architectural connection.'}}]})
            self.assertEqual(body, {'text':'Edited commentary','voice_id':'stella','format':'wav'})
            return httpx.Response(200, content=wav_bytes())
        def client():
            return httpx.Client(base_url='https://api.deepseek.com', transport=httpx.MockTransport(handler))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'chunk.wav'
            path.write_bytes(wav_bytes())
            with patch('backend.services.asr_service.client',client):
                self.assertEqual(transcribe([path,path]), 'Part 1\n\nPart 2')
            with patch('backend.services.commentary_service.client',client):
                self.assertTrue(generate('edited transcript'))
            with patch('backend.services.tts_service.client',client):
                synthesize('Edited commentary','stella',Path(folder)/'result.wav')

    def test_incomplete_tts_is_rejected(self):
        def client():
            return httpx.Client(base_url='https://api.deepseek.com',transport=httpx.MockTransport(lambda r:httpx.Response(200,content=wav_bytes()[:-100])))
        with tempfile.TemporaryDirectory() as folder, patch('backend.services.tts_service.client',client):
            target = Path(folder)/'broken.wav'
            with self.assertRaises(Exception):
                synthesize('Hello','stella',target)
            self.assertFalse(target.exists())

    def test_streaming_wav_placeholder_is_normalized(self):
        data = bytearray(wav_bytes())
        data[4:8] = b'\xff' * 4
        data[40:44] = b'\xff' * 4
        def client():
            return httpx.Client(base_url='https://api.deepseek.com',transport=httpx.MockTransport(lambda r:httpx.Response(200,content=bytes(data))))
        with tempfile.TemporaryDirectory() as folder, patch('backend.services.tts_service.client',client):
            target = Path(folder)/'stream.wav'
            synthesize('Hello','stella',target)
            with wave.open(str(target),'rb') as audio:
                self.assertEqual(audio.getnframes(),16000)

    def test_endpoints_and_missing_key(self):
        with TestClient(app) as api:
            self.assertEqual(api.get('/api/health').status_code,200)
            self.assertEqual(api.post('/api/synthesize',json={'text':'Hello','voice':'invalid'}).status_code,422)
            with patch.dict(os.environ, {'DEEPSEEK_API_KEY':''}):
                self.assertEqual(api.post('/api/commentary',json={'text':'Some speech'}).status_code,503)
            with patch('backend.main.generate',return_value='Real service mocked only in test'):
                self.assertEqual(api.post('/api/commentary',json={'text':'Latest edit'}).status_code,200)
            self.assertEqual(api.get('/api/audio/missing.wav').status_code,404)

if __name__ == '__main__':
    unittest.main()
