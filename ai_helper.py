"""
AI helper — распознавание еды через OpenAI GPT-4o.
Работает с текстом и фото.
"""
import os, json, base64, requests

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_KEY_HERE")
HEADERS = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
API_URL = "https://api.openai.com/v1/chat/completions"

SYSTEM_PROMPT = """Ты диетолог-ассистент. Пользователь описывает еду текстом или присылает фото.
Твоя задача — определить КБЖУ и вернуть ТОЛЬКО JSON без лишнего текста:
{
  "name": "название блюда",
  "kcal": 350,
  "protein": 25.0,
  "fat": 10.0,
  "carbs": 40.0,
  "comment": "короткий игровой комментарий (1 предложение, мотивирующий)"
}
Если еда вредная — мягко пошути об этом в comment. Если полезная — похвали."""


def analyze_food_text(text: str) -> dict | None:
    """Analyze food from text description."""
    try:
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Еда: {text}"}
            ],
            "max_tokens": 200,
        }
        r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=15)
        raw = r.json()["choices"][0]["message"]["content"]
        raw = raw.replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"AI text error: {e}")
        return None


def analyze_food_photo(photo_bytes: bytes) -> dict | None:
    """Analyze food from photo bytes."""
    try:
        b64 = base64.b64encode(photo_bytes).decode()
        payload = {
            "model": "gpt-4o",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text",      "text": SYSTEM_PROMPT + "\nОпредели еду на фото и верни JSON."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ]
            }],
            "max_tokens": 300,
        }
        r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=20)
        raw = r.json()["choices"][0]["message"]["content"]
        raw = raw.replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"AI photo error: {e}")
        return None
