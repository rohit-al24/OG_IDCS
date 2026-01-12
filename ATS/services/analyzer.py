import os
import requests
import time
import json
from decouple import config

# Helper to call OpenAI GPT API (or Perplexity API)
def call_ai_api(prompt: str, max_retries: int = 3, timeout: int = 20) -> str:
    """
    Sends a prompt to the Perplexity API and returns the response text.
    Reads API key from env (PERPLEXITY_API_KEY).
    """
    api_key = config('PERPLEXITY_API_KEY', default=None) or os.environ.get('PERPLEXITY_API_KEY')
    if not api_key:
        raise RuntimeError('PERPLEXITY_API_KEY not set in environment or .env')

    url = 'https://api.perplexity.ai/chat/completions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    data = {
        'model': 'sonar-pro',
        'messages': [
            {'role': 'system', 'content': 'You are an expert resume reviewer and ATS analyzer.'},
            {'role': 'user', 'content': prompt}
        ],
        'max_tokens': 256,
        'temperature': 0.2,
    }
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=timeout)
            resp.raise_for_status()
            result = resp.json()
            # Perplexity returns similar structure to OpenAI
            return result['choices'][0]['message']['content']
        except Exception as e:
            last_err = e
            time.sleep(1 + attempt)
    raise RuntimeError(f'AI API call failed after {max_retries} attempts: {last_err}')

# Modular: can add Perplexity or other APIs here later
