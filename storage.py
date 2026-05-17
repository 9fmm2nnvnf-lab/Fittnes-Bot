import json
import os
from typing import Optional

DATA_DIR  = os.path.join(os.path.dirname(__file__), "data")
DATA_FILE = os.path.join(DATA_DIR, "users.json")


def _load_all() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_all(data: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user(user_id: int) -> Optional[dict]:
    data = _load_all()
    return data.get(str(user_id))


def save_user(user_id: int, char: dict) -> None:
    data = _load_all()
    data[str(user_id)] = char
    _save_all(data)


def user_exists(user_id: int) -> bool:
    return get_user(user_id) is not None
