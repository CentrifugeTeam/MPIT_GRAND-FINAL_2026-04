"""
Шаг 2 пайплайна: выбор шаблона под тип вопроса или свободная формулировка для LLM.
Расширяйте ключевыми словами под домен заказчика.
"""

from typing import Optional, Tuple


def resolve_template(question: str) -> Tuple[Optional[str], str]:
    q = question.lower().strip()
    if any(w in q for w in ("продаж", "выручк", "revenue", "sales")):
        return ("sales_metrics", question)
    if any(w in q for w in ("маркетинг", "реклам", "канал", "campaign")):
        return ("marketing", question)
    if any(w in q for w in ("динамик", "по месяц", "по дням", "тренд")):
        return ("time_series", question)
    return (None, question)
