# 🤖 Fiverr Notifier

Личный робот, который следит за почтой Gmail и мгновенно присылает в Telegram
уведомления о событиях на **Fiverr**: новые сообщения, заказы, отзывы, дедлайны и т.д.
Опционально использует бесплатный AI (Google Gemini) для короткой выжимки и оценки срочности.

## Как это работает

```
Fiverr → письмо на Gmail → робот читает (IMAP) → определяет тип события
       → AI делает выжимку → присылает уведомление в Telegram
```

## Установка

1. Установить Python 3.10+ (https://python.org).
2. В папке проекта выполнить:
   ```
   pip install -r requirements.txt
   ```
3. Скопировать `.env.example` в `.env` и заполнить значения.

## Что нужно вписать в `.env`

| Параметр | Где взять |
|---|---|
| `TELEGRAM_BOT_TOKEN` | у @BotFather в Telegram (`/newbot`) |
| `TELEGRAM_CHAT_ID` | `python main.py --setup` (после того как напишешь боту) |
| `GMAIL_ADDRESS` | твой адрес Gmail |
| `GMAIL_APP_PASSWORD` | App Password в настройках Google (не обычный пароль) |
| `GEMINI_API_KEY` | https://aistudio.google.com/app/apikey (бесплатно) |

## Запуск

```
python main.py --setup    # помощник настройки: chat_id + проверка подключений
python main.py --once      # один тестовый проход
python main.py             # рабочий режим (проверка каждые 30 сек)
```

## Структура

| Файл | Назначение |
|---|---|
| `main.py` | точка входа и главный цикл |
| `config.py` | настройки из `.env` |
| `mail_reader.py` | чтение писем из Gmail (IMAP) |
| `parser.py` | определение типа события Fiverr |
| `ai_processor.py` | AI-выжимка через Gemini |
| `telegram_sender.py` | отправка в Telegram |
| `state.py` | память (защита от дублей) |
