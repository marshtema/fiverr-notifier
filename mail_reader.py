"""Модуль 1: подключение к Gmail по IMAP и чтение новых писем от Fiverr."""
import socket
from dataclasses import dataclass

from imap_tools import MailBox, AND

import config

# Защита от зависаний: любая сетевая операция оборвётся по таймауту,
# а не будет висеть вечно (критично для GitHub Actions).
IMAP_TIMEOUT = 25
socket.setdefaulttimeout(IMAP_TIMEOUT)

# Максимум писем за один проход (защита от выкачивания всего ящика).
FETCH_LIMIT = 40


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


def _login() -> MailBox:
    """Логин в Gmail с таймаутом подключения."""
    return MailBox(config.IMAP_SERVER, timeout=IMAP_TIMEOUT).login(
        config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD
    )


def fetch_new_fiverr_emails() -> list[Email]:
    """Берёт непрочитанные письма ТОЛЬКО от Fiverr.

    Важно: фильтр по отправителю (from "fiverr") выполняется на стороне Gmail —
    скачиваются только письма Fiverr, а не весь непрочитанный ящик. Это убирает
    зависания на больших ящиках.
    """
    results: list[Email] = []
    with _login() as mailbox:
        # Сервер Gmail сам отбирает: непрочитанные + от отправителя с "fiverr".
        # reverse=True -> сначала самые новые; limit -> не больше FETCH_LIMIT.
        criteria = AND(seen=False, from_="fiverr")
        for msg in mailbox.fetch(
            criteria, mark_seen=False, bulk=True,
            limit=FETCH_LIMIT, reverse=True,
        ):
            if not _looks_like_fiverr(msg.from_):
                continue  # доп. страховка
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

    Это защита от дублей в облачном режиме (GitHub Actions), где нет
    постоянного state.json между запусками.
    """
    if not uids:
        return
    from imap_tools import MailMessageFlags
    with _login() as mailbox:
        mailbox.flag(uids, MailMessageFlags.SEEN, True)


def test_connection() -> tuple[bool, str]:
    """Проверка логина в Gmail. Возвращает (успех, сообщение)."""
    try:
        with _login():
            return True, "Gmail: подключение успешно"
    except Exception as e:  # noqa: BLE001
        return False, f"Gmail: ошибка подключения — {e}"
