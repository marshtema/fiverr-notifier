"""Модуль 2: определение типа события Fiverr и его важности.

Главная задача — отделить ВАЖНОЕ (заказы, сообщения клиентов, отзывы, дедлайны)
от ШУМА (сброс пароля, вход в аккаунт, новости, акции, статистика и т.п.).
В Telegram уходят только важные события.
"""
import re
from dataclasses import dataclass

import config
from mail_reader import Email


@dataclass
class Event:
    type: str          # машинный код события
    title: str         # заголовок для уведомления
    emoji: str         # эмодзи для уведомления
    sender_name: str   # имя клиента, если удалось вытащить
    important: bool     # слать ли уведомление
    raw_subject: str
    raw_text: str


# --- ШУМ: если тема письма содержит что-то из этого — НЕ уведомляем. ---
# Проверяется ПЕРВЫМ, до правил важности.
NOISE_KEYWORDS = [
    # Безопасность / аккаунт
    "reset your password", "reset your fiverr password", "password",
    "verify", "verification", "confirm your email", "email address",
    "connected to your", "is now connected", "linked to your",
    "phone number was added", "phone number", "new phone",
    "new device", "new login", "logged in", "signed in", "sign-in",
    "sign in", "login attempt", "security alert", "two-factor", "2fa",
    "successfully", "has been changed", "was changed", "account settings",
    # Новости / маркетинг / обучение
    "newsletter", "weekly", "digest", "tips", "trending", "inspiration",
    "discover", "recommended for you", "promo", "promotion", "sale",
    "discount", "% off", "coupon", "deal", "webinar", "blog",
    "fiverr learn", "course", "survey", "complete your profile",
    "finish setting up", "get started", "welcome to fiverr",
    # Статистика гигов
    "people viewed", "impressions", "gig stats", "performance",
    "your gig was", "gig was paused", "ranking",
]

# --- ВАЖНОЕ: (код, эмодзи, заголовок, ключевые слова в теме). ---
# Первое совпадение выигрывает.
IMPORTANT_RULES = [
    ("new_order",       "🛒", "НОВЫЙ ЗАКАЗ",
     ["new order", "received an order", "received a new order", "order confirmed",
      "placed an order", "you have a new order", "order from"]),
    ("requirements",    "📋", "ТРЕБОВАНИЯ К ЗАКАЗУ",
     ["requirement", "submit requirements", "waiting for your", "needs your input"]),
    ("delivery_due",    "⏰", "ДЕДЛАЙН ПО ЗАКАЗУ",
     ["is due", "delivery is", "running out", "deadline", "late delivery",
      "order is late", "time to deliver"]),
    ("order_completed", "✅", "ЗАКАЗ ЗАВЕРШЁН",
     ["order completed", "marked as complete", "order delivered",
      "auto-complete", "order was completed"]),
    ("review",          "⭐", "НОВЫЙ ОТЗЫВ",
     ["left you a review", "left a review", "rated you", "new review",
      "received a review", "feedback from"]),
    ("cancellation",    "❌", "ОТМЕНА / СПОР",
     ["cancel", "dispute", "resolution", "refund"]),
    ("offer",           "📨", "ОТВЕТ НА ОФФЕР / БРИФ",
     ["custom offer", "buyer request", "your brief", "responded to your offer"]),
    ("new_message",     "💬", "НОВОЕ СООБЩЕНИЕ",
     ["new message", "sent you a message", "you have a message",
      "you have an unread", "unread message", "replied to you", "sent you"]),
]


def _extract_sender_name(subject: str) -> str:
    """Пытаемся вытащить имя клиента из темы письма."""
    patterns = [
        r"from\s+([A-Za-z0-9_.\-]+)",
        r"([A-Za-z0-9_.\-]+)\s+sent you",
        r"([A-Za-z0-9_.\-]+)\s+placed",
        r"([A-Za-z0-9_.\-]+)\s+left you",
        r"([A-Za-z0-9_.\-]+)\s+rated",
    ]
    for p in patterns:
        m = re.search(p, subject, flags=re.IGNORECASE)
        if m:
            name = m.group(1)
            if name.lower() not in ("you", "your", "the", "a", "fiverr"):
                return name
    return ""


def _is_noise(subject_l: str) -> bool:
    return any(kw in subject_l for kw in NOISE_KEYWORDS)


def classify(email: Email) -> Event:
    subject_l = email.subject.lower()
    sender = _extract_sender_name(email.subject)

    # 1) Сначала отсекаем шум.
    if _is_noise(subject_l):
        return Event(
            type="noise", title="ШУМ FIVERR", emoji="🔕",
            sender_name=sender, important=False,
            raw_subject=email.subject, raw_text=email.text,
        )

    # 2) Ищем важное событие.
    for code, emoji, title, keywords in IMPORTANT_RULES:
        if any(kw in subject_l for kw in keywords):
            return Event(
                type=code, title=title, emoji=emoji,
                sender_name=sender, important=True,
                raw_subject=email.subject, raw_text=email.text,
            )

    # 3) Неопознанное письмо от Fiverr.
    #    По умолчанию НЕ шлём (чтобы не было мусора), но можно включить
    #    NOTIFY_UNKNOWN=true в .env, если хочешь видеть и такие.
    return Event(
        type="other", title="УВЕДОМЛЕНИЕ FIVERR", emoji="🔔",
        sender_name=sender, important=config.NOTIFY_UNKNOWN,
        raw_subject=email.subject, raw_text=email.text,
    )
