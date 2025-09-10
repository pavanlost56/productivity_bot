from __future__ import annotations
import os, json, re
import google.generativeai as genai
from openai import OpenAI
from .config import OPENAI_API_KEY

# === Gemini setup ===
if os.getenv("GEMINI_API_KEY"):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
else:
    _gemini_model = None

# === OpenAI setup ===
_openai = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

PROMPT = """You are a date/time and task extraction assistant.
Input: "{text}"
Output JSON with fields:
{
  "title": "<task title>",
  "start": "<YYYY-MM-DD HH:MM>",
  "end": "<YYYY-MM-DD HH:MM>"
}
If end time not specified, set 1 hour after start.
Always return valid JSON only.
"""

def parse_task(text: str, tz: str = "Asia/Kolkata") -> dict | None:
    """Parse natural language text into task dict."""
    raw = None
    try:
        if _gemini_model:
            resp = _gemini_model.generate_content(PROMPT.format(text=text))
            raw = resp.text
        elif _openai:
            resp = _openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": PROMPT.format(text=text)}],
                temperature=0,
            )
            raw = resp.choices[0].message.content
        else:
            raise RuntimeError("No LLM configured (Gemini or OpenAI key missing)")
    except Exception as e:
        print("Parse task failed:", e)
        return None

    # Extract JSON from response
    try:
        match = re.search(r"\{.*\}", raw, re.S)
        data = json.loads(match.group(0)) if match else None
        return data
    except Exception as e:
        print("Invalid JSON parse:", raw, e)
        return None
