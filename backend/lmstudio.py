import json
import os
import re

import httpx
from dotenv import load_dotenv

load_dotenv()

LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234")
TIMEOUT = 60.0

SYSTEM_PROMPT = """You are a fragrance formula extraction engine.

Extract fragrance formula information from the conversation provided.

Return JSON only. No explanation. No markdown. No code fences.

Schema:
{
  "is_formula": true,
  "formula_name": "",
  "version": "",
  "description": "",
  "ingredients": [
    {
      "ingredient": "",
      "pct": 0,
      "concentration": 10
    }
  ]
}

Rules:
- description: one sentence summarising the character or intent of the formula (e.g. "Woody chypre with a floral heart"). Leave empty string if nothing can be inferred.
- version: use "1" if not explicitly stated.
- concentration: stock solution strength as a number (100 = neat/undiluted, 10 = 10% dilution, 1 = 1%, 0.1 = 0.1%, 0.01 = 0.01%). Priority: (1) if the conversation explicitly states a dilution for a specific ingredient (e.g. "10% solution", "diluted to 1%", "in IPM"), use that value for that ingredient. (2) For all remaining ingredients where no dilution is mentioned, if the formula percentages sum to approximately 100%, use 100. (3) Otherwise default to 10.

If no formula is present, return:
{"is_formula": false, "formula_name": "", "version": "", "description": "", "ingredients": []}"""


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_formula(conversation_text: str) -> dict:
    """Send conversation text to LM Studio and return extracted formula as dict.

    Raises ValueError on non-JSON or malformed response.
    Raises httpx.HTTPError on connection failure.
    """
    url = f"{LMSTUDIO_BASE_URL}/v1/chat/completions"
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": conversation_text},
        ],
        "temperature": 0.0,
        "stream": False,
    }

    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()

    data = response.json()
    raw_content = data["choices"][0]["message"]["content"]
    cleaned = _strip_code_fences(raw_content)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LM Studio returned non-JSON response: {cleaned!r}") from exc


if __name__ == "__main__":
    # Standalone verification — run with: python backend/lmstudio.py
    sample = """
user: I've been working on a new chypre. Here's what I have so far:
- Iso E Super 40%
- Hedione 25%
- Linalool 15%
- Bergamot 20%
I'm calling it 'Forest Chypre' version 2.

assistant: That sounds like a lovely composition! The Iso E Super will give it a nice woody backbone.

user: #SAVE_FORMULA
"""
    result = extract_formula(sample)
    print(json.dumps(result, indent=2))
