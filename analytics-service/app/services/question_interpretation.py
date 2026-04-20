"""
Оценка неоднозначности запроса: confidence + предупреждения без вызова LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class InterpretationResult:
    """Результат эвристического разбора вопроса."""

    confidence: float
    warnings: list[str]
    suggestions: list[str]


_TIME_HINTS = (
    "20",
    "19",
    "год",
    "месяц",
    "квартал",
    "недел",
    "день",
    "сутк",
    "час",
    "за ",
    "с ",
    " по ",
    "январ",
    "феврал",
    "март",
    "апрел",
    "мая",
    "июн",
    "июл",
    "август",
    "сентябр",
    "октябр",
    "ноябр",
    "декабр",
    "q1",
    "q2",
    "q3",
    "q4",
    "ytd",
    "mtd",
    "today",
    "вчера",
    "позавчера",
    "прошл",
    "текущ",
)

_DYNAMICS_HINTS = (
    "динамик",
    "тренд",
    "изменен",
    "рост",
    "паден",
    "растёт",
    "падает",
    "конверс",
    "продаж",
    "выручк",
    "объём",
    "объем",
    "сравн",
    "доля",
    "структур",
)

_VAGUE_PTR = (" это ", " там ", "то же", "как там", "те же", "этот ", "ту ", "тех ")


def analyze_question(question: str) -> InterpretationResult:
    q = question.strip()
    if not q:
        return InterpretationResult(
            0.2,
            ["Пустой запрос."],
            ["Сформулируйте вопрос полными словами."],
        )

    ql = f" {q.lower()} "
    warnings: list[str] = []
    suggestions: list[str] = []
    penalty = 0.0

    words = q.split()
    if len(words) <= 2:
        penalty += 0.28
        warnings.append("Запрос очень короткий — контекста может не хватить для точного SQL.")
        suggestions.append(
            "Уточните метрику и объект (например: «сумма заказов по регионам за прошлый месяц»)."
        )

    if len(words) > 55:
        penalty += 0.06
        warnings.append("Очень длинная формулировка — возможно, несколько задач в одном сообщении.")

    needs_time = any(h in ql for h in _DYNAMICS_HINTS)
    has_time = any(h in ql for h in _TIME_HINTS)
    if needs_time and not has_time:
        penalty += 0.22
        warnings.append(
            "Запрос похож на динамику или сравнение во времени, но период не указан явно."
        )
        suggestions.append(
            "Добавьте период: «за 2024 год», «по месяцам», «за последние 30 дней»."
        )

    qmarks = q.count("?")
    if qmarks > 1:
        penalty += 0.14
        warnings.append("В тексте несколько вопросов — лучше разбить на отдельные запросы.")

    if any(p in ql for p in _VAGUE_PTR):
        penalty += 0.1
        warnings.append("Есть указательные слова («это», «там») без явного объекта.")

    # Нет ни одной цифры и нет календарных слов — для фильтров часто полезно
    if not re.search(r"\d", q) and not has_time and len(words) >= 4:
        penalty += 0.06
        suggestions.append(
            "При необходимости укажите числовой фильтр или дату (например «более 100» или «после 01.01.2024»)."
        )

    # Противоречивые гранулярности
    if "по дням" in ql and "по годам" in ql:
        penalty += 0.12
        warnings.append("Указаны разные уровни агрегации времени (день и год) — уточните одну.")

    confidence = max(0.12, min(1.0, 1.0 - penalty))
    if not suggestions and confidence < 0.85:
        suggestions.append(
            "При сомнениях переформулируйте: метрика + срез (группировка) + период + фильтры."
        )

    return InterpretationResult(
        round(confidence, 3),
        warnings,
        suggestions,
    )
