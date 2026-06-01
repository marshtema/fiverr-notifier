"""Модуль 3: AI-обработка письма через бесплатный Google Gemini.

Делает короткую выжимку и оценивает срочность. Если AI выключен или упал —
аккуратно возвращает None, и программа продолжит работать без AI.
"""
import re
from dataclasses import dataclass

import config

_model = None  # ленивая инициализация


@dataclass
class AIResult:
    summary: str        # короткая выжимка сути
    urgency: str        # "high" | "normal" | "low"


def _clean_text(text: str, limit: int = 4000) -> str:
    """Убираем лишние пустые строки и обрезаем очень длинные письма."""
    text = re.sub(r"\n{3,}", "\n\n", text or "")
    return text[:limit]


def _get_model():
    global _model
    if _model is not None:
        return _model
    import google.generativeai as genai
    genai.configure(api_key=config.GEMINI_API_KEY)
    _model = genai.GenerativeModel(config.GEMINI_MODEL)
    return _model


def process(event_title: str, subject: str, text: str) -> AIResult | None:
    """Возвращает выжимку и срочность, либо None при ошибке/выключенном AI."""
    if not config.AI_ENABLED or not config.GEMINI_API_KEY:
        return None

    lang = "русском" if config.NOTIFY_LANGUAGE == "ru" else "английском"
    prompt = f"""Ты помощник фрилансера на Fiverr. Пришло письмо-уведомление.
Тип события: {event_title}
Тема письма: {subject}
Текст письма:
{_clean_text(text)}

Сделай ДВЕ вещи на {lang} языке:
1. Очень короткая выжимка сути (1-2 предложения, по делу: что хотят, бюджет/дедлайн если есть).
2. Срочность: ответь одним словом — high, normal или low.

Формат ответа строго такой:
SUMMARY: <выжимка>
URGENCY: <high|normal|low>"""

    try:
        model = _get_model()
        resp = model.generate_content(prompt)
        raw = (resp.text or "").strip()
    except Exception as e:  # noqa: BLE001
        print(f"[AI] ошибка, пропускаю выжимку: {e}")
        return None

    summary = ""
    urgency = "normal"
    for line in raw.splitlines():
        line = line.strip()
        if line.upper().startswith("SUMMARY:"):
            summary = line.split(":", 1)[1].strip()
        elif line.upper().startswith("URGENCY:"):
            u = line.split(":", 1)[1].strip().lower()
            if u in ("high", "normal", "low"):
                urgency = u

    if not summary:
        summary = raw[:300]
    return AIResult(summary=summary, urgency=urgency)
