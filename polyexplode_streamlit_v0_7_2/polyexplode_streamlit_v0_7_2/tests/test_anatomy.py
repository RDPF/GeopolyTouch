from __future__ import annotations

from polyexplode.anatomy import (
    automatic_explanation,
    build_html_report,
    piece_rows,
    reliability_tag,
    teacher_questions,
)
from polyexplode.core import build_solid_from_definition
from polyexplode.solids import get_solid_definition


def test_piece_rows_match_faces_and_volume():
    model = build_solid_from_definition(get_solid_definition("Dodecaedro"))
    rows = piece_rows(model)
    assert len(rows) == len(model.faces)
    assert all(row["Volume da peça"] > 0 for row in rows)
    total = sum(row["Volume da peça"] for row in rows)
    assert abs(total - model.volume) < 1e-4


def test_automatic_explanation_mentions_euler_and_pieces():
    model = build_solid_from_definition(get_solid_definition("Cubo"))
    text = automatic_explanation(model)
    assert "χ = 2" in text
    assert "6 peças" in text
    assert "Octaedro" in text


def test_teacher_questions_have_answers():
    model = build_solid_from_definition(get_solid_definition("Icosaedro"))
    questions = teacher_questions(model)
    assert len(questions) >= 5
    assert all("Pergunta" in item and "Resposta esperada" in item for item in questions)


def test_html_report_is_complete_document():
    model = build_solid_from_definition(get_solid_definition("Tetraedro"))
    html = build_html_report(model)
    assert html.startswith("<!doctype html>")
    assert "Relatório PolyExplode" in html
    assert "Anatomia das peças" in html
    assert "Modo professor" in html


def test_reliability_tag_for_johnson_is_didactic():
    model = build_solid_from_definition(get_solid_definition("J4 Cúpula quadrada"))
    tag, note = reliability_tag(model)
    assert tag == "topológico-didático"
    assert note
