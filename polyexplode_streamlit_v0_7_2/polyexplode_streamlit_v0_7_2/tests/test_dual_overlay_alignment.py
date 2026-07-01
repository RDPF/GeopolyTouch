from __future__ import annotations

import numpy as np

from polyexplode.core import build_dual_graph, build_solid_from_definition, face_matches_filter
from polyexplode.render_plotly import RenderOptions, build_figure
from polyexplode.solids import get_solid_definition


def test_dual_graph_can_follow_exploded_faces():
    model = build_solid_from_definition(get_solid_definition("Dodecaedro"))
    explosion = 0.70
    fixed = build_dual_graph(model, outward_scale=1.07, explosion=explosion, follow_explosion=False)
    following = build_dual_graph(model, outward_scale=1.07, explosion=explosion, follow_explosion=True, progress=1.0)

    for idx, face in enumerate(model.faces):
        expected_shift = face.normal * explosion * model.radius
        assert np.allclose(following.vertices[idx], fixed.vertices[idx] + expected_shift)


def test_dual_follow_respects_face_filter():
    model = build_solid_from_definition(get_solid_definition("Cuboctaedro"))
    explosion = 0.90
    face_filter = "Triângulos"
    fixed = build_dual_graph(model, outward_scale=1.07, explosion=explosion, face_filter=face_filter, follow_explosion=False)
    following = build_dual_graph(model, outward_scale=1.07, explosion=explosion, face_filter=face_filter, follow_explosion=True, progress=1.0)

    shifted = 0
    unshifted = 0
    for idx, face in enumerate(model.faces):
        delta = following.vertices[idx] - fixed.vertices[idx]
        if face_matches_filter(face, face_filter):
            shifted += 1
            assert np.linalg.norm(delta) > 0.25 * model.radius
            assert np.allclose(delta, face.normal * explosion * model.radius)
        else:
            unshifted += 1
            assert np.allclose(delta, np.zeros(3))
    assert shifted > 0 and unshifted > 0


def test_build_figure_dual_overlay_changes_when_following_explosion():
    model = build_solid_from_definition(get_solid_definition("Dodecaedro"))
    fixed_fig = build_figure(model, RenderOptions(explosion=0.85, show_dual=True, dual_follow_explosion=False, show_ghost=False, show_edges=False))
    follow_fig = build_figure(model, RenderOptions(explosion=0.85, show_dual=True, dual_follow_explosion=True, show_ghost=False, show_edges=False))

    def dual_marker_xyz(fig):
        for trace in fig.data:
            if getattr(trace, "name", "") == "Vértices do dual":
                return np.array(trace.x, dtype=float), np.array(trace.y, dtype=float), np.array(trace.z, dtype=float)
        raise AssertionError("dual marker trace not found")

    fx, fy, fz = dual_marker_xyz(fixed_fig)
    gx, gy, gz = dual_marker_xyz(follow_fig)
    fixed_radius = np.sqrt(fx**2 + fy**2 + fz**2).mean()
    follow_radius = np.sqrt(gx**2 + gy**2 + gz**2).mean()
    assert follow_radius > fixed_radius * 1.35
