import os
import httpx
from fastapi import HTTPException

def client():
    key = os.getenv('DEEPSEEK_API_KEY', '').strip()
    if not key:
        raise HTTPException(503, 'DEEPSEEK_API_KEY is missing. Configure .env and restart the backend, then retry.')
    return httpx.Client(base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com').rstrip('/'), headers={'Authorization': f'Bearer {key}'}, timeout=httpx.Timeout(600, connect=20))

def check(response):
    if response.is_error:
        raise HTTPException(502, f'DeepSeek returned HTTP {response.status_code}. Check your API access, balance and connection, then retry.')
