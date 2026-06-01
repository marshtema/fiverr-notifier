"""Модуль 4: отправка уведомлений в Telegram через Bot API (без лишних зависимостей)."""
import html

import requests

import config

API = "https://api.telegram.org/bot{token}/{method}"

URGENCY_BADGE = {
    "high": "🔴 СРОЧНО",
    "normal": "🟡 обычное",
    "low": "🟢 не срочно",
}


def _api(method: str, payload: dict) -> dict:
    url = API.format(token=config.TELEGRAM_BOT_TOKEN, method=method)
    resp = requests.post(url, json=payload, timeout=20)
    return resp.json()


def send_notification(event, ai_result, fiverr_url: str = "https://www.fiverr.com/inbox") -> bool:
    """Собирает красивое сообщение и отправляет его в Telegram."""
    e = html.escape

    lines = [f"{event.emoji} <b>{e(event.title)}</b>"]

    if event.sender_name:
        lines.append(f"👤 От: <b>{e(event.sender_name)}</b>")

    if ai_result:
        lines.append("")
        lines.append(f"📝 {e(ai_result.summary)}")
        badge = URGENCY_BADGE.get(ai_result.urgency, "")
        if badge:
            lines.append(f"Приоритет: {badge}")
    else:
        # AI выключен/недоступен — показываем тему письма.
        lines.append("")
        lines.append(f"✉️ {e(event.raw_subject)}")

    text = "\n".join(lines)

    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "🔗 Открыть на Fiverr", "url": fiverr_url}
            ]]
        },
    }
    result = _api("sendMessage", payload)
    if not result.get("ok"):
        print(f"[Telegram] ошибка отправки: {result}")
        return False
    return True


def send_plain(text: str) -> bool:
    """Простое текстовое сообщение (для статусов запуска)."""
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    result = _api("sendMessage", payload)
    return bool(result.get("ok"))


def get_chat_id_from_updates() -> str | None:
    """Берёт chat_id из последнего сообщения, отправленного боту.

    Нужно один раз написать боту /start, потом вызвать эту функцию.
    """
    url = API.format(token=config.TELEGRAM_BOT_TOKEN, method="getUpdates")
    resp = requests.get(url, timeout=20).json()
    if not resp.get("ok"):
        print(f"[Telegram] getUpdates ошибка: {resp}")
        return None
    updates = resp.get("result", [])
    for upd in reversed(updates):
        msg = upd.get("message") or upd.get("edited_message")
        if msg and msg.get("chat"):
            return str(msg["chat"]["id"])
    return None
