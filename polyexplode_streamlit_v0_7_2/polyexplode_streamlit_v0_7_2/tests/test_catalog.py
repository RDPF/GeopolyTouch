from __future__ import annotations

from polyexplode.core import build_dual_graph, build_solid_from_definition, face_filter_options
from polyexplode.render_plotly import RenderOptions, build_figure
from polyexplode.solids import SOLID_NAMES, get_solid_definition


def test_catalog_size():
    assert len(SOLID_NAMES) == 48


def test_all_solids_build_with_euler_and_positive_volume():
    for name in SOLID_NAMES:
        model = build_solid_from_definition(get_solid_definition(name))
        assert len(model.vertices) >= 4, name
        assert len(model.faces) >= 4, name
        assert model.edge_count > 0, name
        assert model.euler_characteristic == 2, name
        assert model.volume > 0, name


def test_face_filters_include_all():
    for name in SOLID_NAMES:
        model = build_solid_from_definition(get_solid_definition(name))
        options = face_filter_options(model)
        assert options[0] == "Todas", name
        assert len(options) >= 2, name


def test_dual_graph_consistency():
    for name in SOLID_NAMES:
        model = build_solid_from_definition(get_solid_definition(name))
        dual = build_dual_graph(model)
        assert len(dual.vertices) == len(model.faces), name
        assert len(dual.edges) > 0, name
        assert len(dual.edges) <= model.edge_count, name


def test_plotly_figure_builds_for_dodecahedron():
    model = build_solid_from_definition(get_solid_definition("Dodecaedro"))
    fig = build_figure(model, RenderOptions(explosion=0.8, show_dual=True, show_normals=True))
    assert len(fig.data) > len(model.faces)
