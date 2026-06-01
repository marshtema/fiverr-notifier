"""Модуль 1: подключение к Gmail по IMAP и чтение новых писем от Fiverr."""
import socket
from dataclasses import dataclass

from imap_tools import MailBox, AND

import config

# Защита от зависаний: любая сетевая операция оборвётся через 30 сек,
# а не будет висеть вечно (важно для надёжности на GitHub Actions).
socket.setdefaulttimeout(30)


@dataclass
class Email:
    """Упрощённое представление письма."""
    uid: str
    subject: str
    from_: str
    text: str
    date: str


def _looks_like_fiverr(from_addr: str) -> bool:
    addr = (from_addr or "").lower()
    return any(kw in addr for kw in config.FIVERR_SENDER_KEYWORDS)


def fetch_new_fiverr_emails() -> list[Email]:
    """Берёт непрочитанные письма от Fiverr.

    Письма НЕ помечаются прочитанными — защита от дублей лежит на state.json,
    чтобы не трогать состояние твоего ящика.
    """
    results: list[Email] = []
    with MailBox(config.IMAP_SERVER).login(
        config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD
    ) as mailbox:
        # seen=False -> только непрочитанные. mark_seen=False -> не помечаем.
        for msg in mailbox.fetch(AND(seen=False), mark_seen=False, bulk=True):
            if not _looks_like_fiverr(msg.from_):
                continue
            body = (msg.text or msg.html or "").strip()
            results.append(
                Email(
                    uid=str(msg.uid),
                    subject=(msg.subject or "").strip(),
                    from_=(msg.from_ or "").strip(),
                    text=body,
                    date=str(msg.date),
                )
            )
    return results


def mark_emails_seen(uids: list[str]) -> None:
    """Помечает письма прочитанными (по UID), чтобы не обрабатывать повторно.

    Используется в облачном режиме (GitHub Actions) как защита от дублей,
    т.к. там нет постоянного state.json между запусками.
    """
    if not uids:
        return
    from imap_tools import MailMessageFlags
    with MailBox(config.IMAP_SERVER).login(
        config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD
    ) as mailbox:
        mailbox.flag(uids, MailMessageFlags.SEEN, True)


def test_connection() -> tuple[bool, str]:
    """Проверка логина в Gmail. Возвращает (успех, сообщение)."""
    try:
        with MailBox(config.IMAP_SERVER).login(
            config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD
        ):
            return True, "Gmail: подключение успешно"
    except Exception as e:  # noqa: BLE001
        return False, f"Gmail: ошибка подключения — {e}"
