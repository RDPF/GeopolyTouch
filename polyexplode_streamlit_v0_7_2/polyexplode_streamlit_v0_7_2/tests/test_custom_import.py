from polyexplode.core import build_solid_from_definition
from polyexplode.custom_import import (
    example_json_tetrahedron,
    example_off_cube,
    import_uploaded_solid,
    parse_json_solid,
    parse_off,
    validate_definition,
)


def test_parse_off_cube_and_validate():
    definition = parse_off(example_off_cube(), "cube.off")
    report = validate_definition(definition, fmt="off")
    assert report.ok_to_build
    assert report.closed_manifold
    assert report.convexity == "convexo provável"
    assert report.euler == 2
    model = build_solid_from_definition(definition)
    assert model.euler_characteristic == 2
    assert model.volume > 0


def test_parse_json_tetrahedron_and_build():
    definition = parse_json_solid(example_json_tetrahedron(), "tetra.json")
    imported = import_uploaded_solid(example_json_tetrahedron(), "tetra.json")
    assert imported.report.ok_to_build
    model = build_solid_from_definition(definition)
    assert len(model.faces) == 4
    assert model.volume > 0


def test_problematic_open_mesh_warns():
    open_off = """OFF
4 3 0
0 0 0
1 0 0
0 1 0
0 0 1
3 0 1 2
3 0 1 3
3 0 2 3
"""
    definition = parse_off(open_off, "open.off")
    report = validate_definition(definition, fmt="off")
    assert report.ok_to_build
    assert not report.closed_manifold
    assert report.has_warnings


def test_malformed_off_is_rejected():
    bad = "OFF\n3 1 0\n0 0 0\n1 0 0\n0 1 0\n3 0 1 9\n"
    try:
        parse_off(bad, "bad.off")
    except ValueError as exc:
        assert "ao menos 4 vértices" in str(exc) or "fora" in str(exc)
    else:
        raise AssertionError("malformed OFF should fail")
