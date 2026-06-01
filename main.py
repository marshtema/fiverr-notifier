"""Fiverr Notifier — главный файл.

Запуск:
  python main.py            # обычный режим (бесконечный цикл проверки почты)
  python main.py --setup    # помощник: найти chat_id и проверить подключения
  python main.py --once     # один проход (для теста)
"""
import sys
import time
import traceback

# Консоль Windows по умолчанию cp1251 и падает на эмодзи — переводим вывод в UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

import config
import state
import mail_reader
import parser as event_parser
import ai_processor
import telegram_sender


def setup():
    """Проверка настроек и поиск Telegram chat_id."""
    print("=== Проверка настроек ===")
    problems = config.validate()
    if problems:
        print("⚠️  Найдены проблемы в .env:")
        for p in problems:
            print(f"   - {p}")
    else:
        print("✅ .env заполнен корректно")

    print("\n=== Поиск Telegram chat_id ===")
    if not config.TELEGRAM_BOT_TOKEN:
        print("Сначала укажи TELEGRAM_BOT_TOKEN в .env")
    else:
        print("Напиши своему боту в Telegram любое сообщение (например /start),")
        print("затем нажми Enter здесь...")
        input()
        chat_id = telegram_sender.get_chat_id_from_updates()
        if chat_id:
            print(f"✅ Твой chat_id: {chat_id}")
            print(f"   Впиши его в .env -> TELEGRAM_CHAT_ID={chat_id}")
        else:
            print("❌ Не нашёл сообщений. Убедись, что написал боту, и повтори.")

    print("\n=== Проверка Gmail ===")
    if config.GMAIL_ADDRESS and config.GMAIL_APP_PASSWORD:
        ok, msg = mail_reader.test_connection()
        print(("✅ " if ok else "❌ ") + msg)
    else:
        print("Укажи GMAIL_ADDRESS и GMAIL_APP_PASSWORD в .env")


def process_once(processed: list[str]) -> list[str]:
    """Один проход по почте. Возвращает обновлённый список обработанных UID."""
    try:
        emails = mail_reader.fetch_new_fiverr_emails()
    except Exception as e:  # noqa: BLE001
        print(f"[mail] ошибка чтения почты: {e}")
        return processed

    new_count = 0
    to_mark_seen: list[str] = []  # обработанные письма (отправленные + мусор)

    for email in emails:
        if email.uid in processed:
            continue

        event = event_parser.classify(email)

        # Не важное (шум / неопознанное) — молча помечаем прочитанным, не шлём.
        if not event.important:
            print(f"  · пропуск (не важное): {email.subject[:60]}")
            processed.append(email.uid)
            to_mark_seen.append(email.uid)
            continue

        # Важное — делаем AI-выжимку (только тут тратим квоту AI) и шлём.
        ai_result = ai_processor.process(event.title, event.raw_subject, event.raw_text)
        sent = telegram_sender.send_notification(event, ai_result)

        if sent:
            print(f"  → отправлено: {event.emoji} {event.title} (uid {email.uid})")
            processed.append(email.uid)
            to_mark_seen.append(email.uid)
            new_count += 1
        else:
            # Отправка не удалась — НЕ помечаем прочитанным, повторим в след. раз.
            print(f"  ✗ не удалось отправить uid {email.uid}, повтор позже")

    # Сохраняем локальную память (для режима цикла на ПК).
    if to_mark_seen:
        state.save_processed(processed)

    # Помечаем прочитанными в Gmail (защита от дублей, особенно для GitHub Actions).
    if config.MARK_SEEN and to_mark_seen:
        try:
            mail_reader.mark_emails_seen(to_mark_seen)
        except Exception as e:  # noqa: BLE001
            print(f"[mail] не удалось пометить прочитанными: {e}")

    return processed


def run_loop():
    problems = config.validate()
    if problems:
        print("⚠️  Нельзя запуститься, проблемы в .env:")
        for p in problems:
            print(f"   - {p}")
        print("Запусти:  python main.py --setup")
        return

    print(f"🤖 Fiverr Notifier запущен. Проверка каждые {config.CHECK_INTERVAL_SECONDS} сек.")
    print(f"   AI: {'включён (' + config.GEMINI_MODEL + ')' if config.AI_ENABLED else 'выключен'}")
    telegram_sender.send_plain("🤖 <b>Fiverr Notifier запущен</b>\nСлежу за почтой Fiverr.")

    processed = state.load_processed()
    while True:
        try:
            processed = process_once(processed)
        except KeyboardInterrupt:
            print("\n⏹  Остановлено пользователем.")
            break
        except Exception:  # noqa: BLE001
            print("[loop] непредвиденная ошибка:")
            traceback.print_exc()
        time.sleep(config.CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    if "--setup" in sys.argv:
        setup()
    elif "--once" in sys.argv:
        process_once(state.load_processed())
    else:
        run_loop()
