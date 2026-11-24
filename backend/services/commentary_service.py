from pathlib import Path
from fastapi import HTTPException
from .provider import client, check

PROMPT = Path(__file__).resolve().parents[1] / 'prompts/commentary_prompt.txt'

def generate(text):
    with client() as api:
        response = api.post('/chat/completions', json={'model':'deepseek-flash', 'thinking':{'type':'disabled'}, 'messages':[{'role':'system','content':PROMPT.read_text(encoding='utf-8')},{'role':'user','content':text}], 'max_tokens':500})
        check(response)
        content = response.json()['choices'][0]['message']['content']
        if not content or not content.strip():
            raise HTTPException(502, 'DeepSeek returned empty commentary. Retry generation.')
        return content.strip()
