from polyexplode.core import build_dual_graph, build_solid_from_definition
from polyexplode.duality import (
    dual_comparison_rows,
    duality_explanation,
    expected_dual_name,
    guided_duality_rows,
    guided_duality_steps,
)
from polyexplode.render_plotly import RenderOptions, build_dual_only_figure, build_duality_animation_figure, build_figure
from polyexplode.solids import get_solid_definition


def model(name="Cubo"):
    return build_solid_from_definition(get_solid_definition(name))


def test_known_dual_name_for_cube():
    assert expected_dual_name(model("Cubo")) == "Octaedro"


def test_dual_graph_vertices_match_original_faces():
    m = model("Dodecaedro")
    dual = build_dual_graph(m)
    assert len(dual.vertices) == len(m.faces)
    assert len(dual.edges) > 0


def test_dual_comparison_rows_have_core_counts():
    m = model("Icosaedro")
    rows = dual_comparison_rows(m)
    assert len(rows) >= 5
    assert rows[1]["Dual visual"] == len(m.faces)


def test_guided_steps_are_progressive():
    steps = guided_duality_steps(model("Tetraedro"))
    assert steps[0].progresso == 0.0
    assert steps[-1].progresso == 1.0
    assert [s.etapa for s in steps] == list(range(1, len(steps) + 1))


def test_guided_rows_and_explanation_are_nonempty():
    m = model("Cuboctaedro")
    assert "dual" in duality_explanation(m).lower()
    assert len(guided_duality_rows(m)) == len(guided_duality_steps(m))


def test_render_accepts_dual_progress():
    m = model("Cubo")
    fig = build_figure(m, RenderOptions(show_dual=True, dual_progress=0.35, height=420))
    assert len(fig.data) > 0


def test_dual_only_and_animation_figures():
    m = model("Octaedro")
    dual_fig = build_dual_only_figure(m, progress=0.8, height=420)
    anim_fig = build_duality_animation_figure(m, RenderOptions(show_dual=True, height=420), steps=5)
    assert len(dual_fig.data) >= 2
    assert len(anim_fig.frames) == 5
