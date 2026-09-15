import math
import os
import aiohttp
import json
import re
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = os.getenv(
    "GEMINI_API_URL",
    "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
)


def clean_json(text):
    """Extract a JSON object from text (handles markdown code blocks and extra content)."""
    text = text.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{[\s\S]*\}", text)
    return match.group(0) if match else text


def normalize_question(question):
    """Validate and normalize a Gemini question response.

    Falls back gracefully when alternatives are missing or incomplete.
    Raises ValueError if the payload is unusable.
    """
    if not isinstance(question, dict) or not question.get("question"):
        raise ValueError("Gemini response missing 'question' field")

    q_type = question.get("type", "open")

    if q_type == "multiple":
        alts = question.get("alternatives")
        if not isinstance(alts, dict):
            question["type"] = "open"
            question["alternatives"] = None
        else:
            filtered = {k: v for k, v in alts.items() if k in "ABCDE" and v}
            if len(filtered) < 2:
                question["type"] = "open"
                question["alternatives"] = None
            else:
                question["alternatives"] = filtered

    correct = question.get("correct", "")
    if not str(correct).strip():
        raise ValueError("Gemini response missing 'correct' field")

    return question


async def generate_gemini_question(subject, content):

    prompt = f"""
Generate ONE high-quality question about:

Subject: {subject}
Content: {content}

Rules:
- Vary difficulty (easy, medium).
- Avoid repetitive questions.
- Question can be open-ended or multiple choice.
- Alternatives must be plausible and shuffled.
- For multiple choice, always provide at least 4 alternatives (A-D).
- Respond ONLY with a valid JSON:

{{
  "type": "open" or "multiple",
  "question": "text",
  "alternatives": {{
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "..."
  }} or null,
  "correct": "text or letter"
}}
"""

    body = {
        "model": "gemini-2.0-flash",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.85,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GEMINI_KEY}",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GEMINI_URL,
                headers=headers,
                json=body,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:

                if resp.status != 200:
                    error_text = await resp.text()
                    raise ValueError(f"Gemini API error (status {resp.status}): {error_text[:200]}")

                raw = await resp.json()

                choices = raw.get("choices", [])
                if not choices:
                    raise ValueError("Gemini returned no choices")

                text = choices[0].get("message", {}).get("content", "")
                if not text:
                    raise ValueError("Gemini returned empty content")

                cleaned_text = clean_json(text)
                question = json.loads(cleaned_text)
                return normalize_question(question)

    except aiohttp.ClientError as e:
        raise ValueError(f"Gemini connection error: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned invalid JSON: {e}")