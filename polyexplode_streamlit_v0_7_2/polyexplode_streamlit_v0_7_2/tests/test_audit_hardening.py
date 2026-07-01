from __future__ import annotations

from polyexplode.anatomy import reliability_tag
from polyexplode.core import build_solid_from_definition
from polyexplode.diagnostics import internal_catalog_validation_rows, validate_built_model
from polyexplode.render_plotly import RenderOptions, build_figure
from polyexplode.solids import EXPERIMENTAL_SOLID_NAMES, SOLID_NAMES, get_solid_definition
from polyexplode.ui import home_card, merged_html_report


def test_internal_catalog_validation_is_systematic():
    rows = internal_catalog_validation_rows()
    assert len(rows) == len(SOLID_NAMES)
    row_by_name = {row["Sólido"]: row for row in rows}
    assert "J6 Rotunda pentagonal" in row_by_name
    assert "J10 Rotunda pentagonal alongada" in row_by_name

    for row in rows:
        if row["Sólido"] in EXPERIMENTAL_SOLID_NAMES:
            assert row["Status"] == "experimental"
            assert row["Malha fechada/manifold"] is False
        else:
            assert row["Status"] not in {"crítico", "atenção"}
            assert row["Malha fechada/manifold"] is True
            assert row["χ"] == 2


def test_j6_j10_are_explicitly_experimental():
    for name in ["J6 Rotunda pentagonal", "J10 Rotunda pentagonal alongada"]:
        model = build_solid_from_definition(get_solid_definition(name))
        tag, note = reliability_tag(model)
        report = validate_built_model(model)
        assert tag == "experimental-auditado"
        assert "experimental" in note.lower()
        assert not report.closed_manifold


def test_adaptive_legend_hides_per_piece_legend_for_large_solids():
    model = build_solid_from_definition(get_solid_definition("Pentakis dodecaedro"))
    fig = build_figure(model, RenderOptions(color_mode="Por peça", adaptive_legend=True, legend_threshold=14))
    assert fig.layout.showlegend is False
    assert all(getattr(trace, "showlegend", None) in (False, None) for trace in fig.data if trace.type == "mesh3d")


def test_silent_mode_hides_legend_labels_and_normals():
    model = build_solid_from_definition(get_solid_definition("Dodecaedro"))
    fig = build_figure(model, RenderOptions(show_normals=True, show_labels=True, silent_mode=True))
    assert fig.layout.showlegend is False
    assert not any(getattr(trace, "mode", "") == "text" for trace in fig.data)
    assert not any(getattr(trace, "name", "") == "Normais externas" for trace in fig.data)


def test_html_helpers_escape_user_visible_strings():
    html = home_card("<Sólido>", "Use <b>texto</b> seguro")
    assert "&lt;Sólido&gt;" in html
    assert "<b>texto</b>" not in html

    model = build_solid_from_definition(get_solid_definition("Cubo"))
    report = merged_html_report(model)
    assert "Higiene de auditoria" in report
    assert "v0.6" in report
    assert "Diagnóstico matemático" in report
