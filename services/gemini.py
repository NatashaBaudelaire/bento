import os
import aiohttp
import json
import re
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
# Note: The URL and model name may need to be updated based on the latest Gemini API specifications.
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"


# This function attempts to extract a valid JSON object from the text, even if it's wrapped in markdown code blocks or contains extra text.
def clean_json(text: str):
    text = text.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{[\s\S]*\}", text)
    return match.group(0) if match else text


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
- Respond ONLY with a valid JSON:

{{
  "type": "open" or "multiple",
  "question": "text",
  "alternatives": {{
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "...",
    "E": "..."
  }} or null,
  "correct": "text or letter"
}}
"""

    body = {
        "model": "gemini-2.0-flash", # Updated to a current model version.
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.85
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GEMINI_KEY}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(GEMINI_URL, headers=headers, json=body) as resp:

            status = resp.status
            raw = await resp.json()

            # Minimum debug to diagnose errors.
            print("=== GEMINI DEBUG ===")
            print("STATUS:", status)
            print(json.dumps(raw, indent=2))
            print("====================")

            if status != 200:
                raise ValueError(f"Gemini API Error. Status: {status}")

            text = raw["choices"][0]["message"].get("content", "")

            cleaned_text = clean_json(text)

            try:
                return json.loads(cleaned_text)
            except Exception as e:
                print("RAW RECEIVED JSON:", text)
                print("CLEANED JSON:", cleaned_text)
                raise ValueError("Gemini did not return a valid JSON.") from e