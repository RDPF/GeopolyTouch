from __future__ import annotations

from polyexplode.core import build_solid_from_definition
from polyexplode.diagnostics import (
    catalog_diagnostic_rows,
    convexity_diagnostic_rows,
    diagnose_model,
    edge_diagnostic_rows,
    face_diagnostic_rows,
    technical_report_html,
)
from polyexplode.solids import EXPERIMENTAL_SOLID_NAMES, SOLID_NAMES, get_solid_definition


def test_dodecahedron_has_clean_diagnostics():
    model = build_solid_from_definition(get_solid_definition("Dodecaedro"))
    report = diagnose_model(model)
    assert report.status == "ok"
    assert report.outward_normals_ok
    assert report.closed_manifold
    assert report.convexity == "convexo provável"
    assert report.max_planarity_error <= 1e-5
    assert report.euler == 2


def test_face_diagnostics_expose_orientation_and_planarity():
    model = build_solid_from_definition(get_solid_definition("Cubo"))
    rows = face_diagnostic_rows(model)
    assert len(rows) == len(model.faces)
    assert all(row["Normal externa?"] for row in rows)
    assert max(row["Planaridade relativa"] for row in rows) <= 1e-5


def test_edge_diagnostics_detect_experimental_nonmanifold_edges():
    model = build_solid_from_definition(get_solid_definition("J6 Rotunda pentagonal"))
    report = diagnose_model(model)
    assert model.name in EXPERIMENTAL_SOLID_NAMES
    assert report.status == "experimental"
    assert not report.closed_manifold
    problem_edges = [row for row in edge_diagnostic_rows(model) if row["Status"] != "OK"]
    assert problem_edges


def test_convexity_rows_have_supporting_plane_flags():
    model = build_solid_from_definition(get_solid_definition("Octaedro"))
    rows = convexity_diagnostic_rows(model)
    assert len(rows) == len(model.faces)
    assert all(row["Plano de suporte?"] for row in rows)


def test_catalog_diagnostic_rows_cover_all_solids():
    rows = catalog_diagnostic_rows()
    assert len(rows) == len(SOLID_NAMES)
    by_name = {row["Sólido"]: row for row in rows}
    assert by_name["Cubo"]["Status"] == "ok"
    assert by_name["J6 Rotunda pentagonal"]["Status"] == "experimental"


def test_technical_html_report_contains_required_sections():
    model = build_solid_from_definition(get_solid_definition("Dodecaedro"))
    html = technical_report_html(model)
    assert "Diagnóstico técnico" in html
    assert "orientação" in html.lower()
    assert "manifoldness" in html.lower()
    assert "Convexidade" in html
