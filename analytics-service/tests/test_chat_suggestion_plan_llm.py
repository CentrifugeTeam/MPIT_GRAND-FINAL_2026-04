from app.services.chat_suggestion_plan_llm import normalize_topics


def test_normalize_topics_limits_and_shapes():
    raw = [
        {
            "topic_key": "sales",
            "topic_label": "Продажи",
            "questions": ["Q1", "Q2", "Q3", "Q4", "Q5"],
        },
        {
            "topic_key": "ops",
            "topic_label": "Операции",
            "questions": ["A1", "A2", "A3", "A4"],
        },
        {
            "topic_key": "bad",
            "topic_label": "Плохая",
            "questions": ["x1", "x2"],
        },
    ]
    out = normalize_topics(raw, fallback_display_name="demo")
    assert len(out) == 2
    assert out[0]["topic_key"] == "sales"
    assert len(out[0]["questions"]) == 4
    assert out[0]["questions"] == ["Q1", "Q2", "Q3", "Q4"]


def test_normalize_topics_fallback_when_empty():
    out = normalize_topics([], fallback_display_name="Warehouse")
    assert len(out) >= 1
    assert all(len(x["questions"]) == 4 for x in out)
