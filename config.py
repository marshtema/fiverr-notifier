"""Конфигурация: читает настройки из файла .env."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _get_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name, str(default)).strip().lower()
    return val in ("1", "true", "yes", "y", "on")


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)).strip())
    except (TypeError, ValueError):
        return default


# Telegram
TELEGRAM_BOT_TOKEN = _get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = _get("TELEGRAM_CHAT_ID")

# Gmail
GMAIL_ADDRESS = _get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = _get("GMAIL_APP_PASSWORD")
IMAP_SERVER = "imap.gmail.com"

# AI
AI_ENABLED = _get_bool("AI_ENABLED", True)
GEMINI_API_KEY = _get("GEMINI_API_KEY")
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-2.0-flash")

# Общее
CHECK_INTERVAL_SECONDS = _get_int("CHECK_INTERVAL_SECONDS", 30)
NOTIFY_LANGUAGE = _get("NOTIFY_LANGUAGE", "ru")

# Слать ли уведомления о неопознанных письмах Fiverr (по умолчанию нет — меньше шума)
NOTIFY_UNKNOWN = _get_bool("NOTIFY_UNKNOWN", False)

# Помечать письма прочитанными после обработки.
# ОБЯЗАТЕЛЬНО true для GitHub Actions (там нет state.json между запусками) —
# именно это защищает от дублей в облачном режиме.
MARK_SEEN = _get_bool("MARK_SEEN", True)

# Отправители, которых считаем за Fiverr (фильтр по адресу)
FIVERR_SENDER_KEYWORDS = ("fiverr.com", "fiverr")


def validate() -> list[str]:
    """Возвращает список проблем в настройках (пустой список = всё ок)."""
    problems = []
    if not TELEGRAM_BOT_TOKEN:
        problems.append("TELEGRAM_BOT_TOKEN не задан (получи у @BotFather)")
    if not GMAIL_ADDRESS:
        problems.append("GMAIL_ADDRESS не задан")
    if not GMAIL_APP_PASSWORD:
        problems.append("GMAIL_APP_PASSWORD не задан (нужен App Password, не обычный пароль)")
    if AI_ENABLED and not GEMINI_API_KEY:
        problems.append("AI_ENABLED=true, но GEMINI_API_KEY не задан "
                        "(получи на https://aistudio.google.com/app/apikey "
                        "или поставь AI_ENABLED=false)")
    return problems
