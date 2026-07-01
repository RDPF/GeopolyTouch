from __future__ import annotations

import json

from polyexplode.core import build_solid_from_definition
from polyexplode.lessons import (
    LESSON_LEVELS,
    build_lesson_html,
    build_lesson_text,
    guided_sequence,
    lesson_json,
    lesson_questions,
    level_profile,
)
from polyexplode.solids import get_solid_definition


def model(name="Dodecaedro"):
    return build_solid_from_definition(get_solid_definition(name))


def test_all_lesson_levels_have_profiles():
    for level in LESSON_LEVELS:
        profile = level_profile(level)
        assert profile.level == level
        assert profile.objectives
        assert profile.vocabulary


def test_guided_sequence_contains_required_flow():
    rows = guided_sequence(model("Cubo"), "Médio")
    joined = " ".join(row["Etapa"] for row in rows)
    assert "Observar" in joined
    assert "Contar" in joined
    assert "Explodir" in joined
    assert "Identificar" in joined
    assert "Comparar" in joined
    assert "Responder" in joined


def test_lesson_questions_have_answers_for_all_levels():
    m = model("Icosaedro")
    for level in LESSON_LEVELS:
        rows = lesson_questions(m, level)
        assert len(rows) >= 3
        assert all(row["Pergunta"] and row["Resposta esperada"] and row["Objetivo"] for row in rows)


def test_lesson_exports_are_complete():
    m = model("Tetraedro")
    html = build_lesson_html(m, "Fundamental")
    txt = build_lesson_text(m, "Fundamental")
    data = json.loads(lesson_json(m, "Fundamental"))
    assert html.startswith("<!doctype html>")
    assert "Atividade guiada" in html
    assert "Perguntas com gabarito" in html
    assert "POLYEXPLODE" in txt
    assert data["level"] == "Fundamental"
    assert data["steps"]
