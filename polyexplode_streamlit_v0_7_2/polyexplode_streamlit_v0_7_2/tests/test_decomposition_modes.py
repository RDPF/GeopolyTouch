from __future__ import annotations

from polyexplode.core import build_solid_from_definition
from polyexplode.decomposition import (
    DECOMPOSITION_MODES,
    connected_face_components,
    decomposition_info,
    decomposition_rows,
    edge_pairs,
    face_layer,
)
from polyexplode.render_plotly import RenderOptions, build_figure
from polyexplode.solids import get_solid_definition


def _cube():
    return build_solid_from_definition(get_solid_definition("Cubo"))


def test_decomposition_modes_are_declared():
    assert DECOMPOSITION_MODES == [
        "Pirâmides face-centro",
        "Faces",
        "Componentes",
        "Camadas",
        "Vértices/arestas/faces",
    ]


def test_components_and_edges_for_cube():
    model = _cube()
    assert len(edge_pairs(model)) == 12
    assert connected_face_components(model) == [[0, 1, 2, 3, 4, 5]]
    info = decomposition_info(model, "Componentes")
    assert info.piece_count == 1
    assert "única componente" in info.warning


def test_layers_exist_for_cube():
    model = _cube()
    layers = {face_layer(model, face) for face in model.faces}
    assert "Camada inferior" in layers
    assert "Camada superior" in layers
    rows = decomposition_rows(model, "Camadas")
    assert rows


def test_topological_mode_counts_vef():
    model = _cube()
    info = decomposition_info(model, "Vértices/arestas/faces")
    assert info.piece_count == 8 + 12 + 6
    rows = decomposition_rows(model, "Vértices/arestas/faces")
    assert {row["Entidade"] for row in rows} == {"Vértices", "Arestas", "Faces"}


def test_plotly_builds_for_all_modes():
    model = _cube()
    for mode in DECOMPOSITION_MODES:
        fig = build_figure(model, RenderOptions(explosion=0.8, decomposition_mode=mode, show_dual=True))
        assert len(fig.data) > 0, mode
        assert mode in fig.layout.title.text
