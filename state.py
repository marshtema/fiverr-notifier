"""Память программы: какие письма уже обработаны (защита от дублей)."""
import json
import os

STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")
MAX_KEEP = 500  # сколько последних UID хранить, чтобы файл не рос бесконечно


def load_processed() -> list[str]:
    if not os.path.exists(STATE_FILE):
        return []
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return list(data.get("processed_uids", []))
    except (json.JSONDecodeError, OSError):
        return []


def save_processed(uids: list[str]) -> None:
    trimmed = uids[-MAX_KEEP:]
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"processed_uids": trimmed}, f, ensure_ascii=False, indent=2)
