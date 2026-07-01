from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Sequence

import numpy as np


PHI = (1.0 + np.sqrt(5.0)) / 2.0


@dataclass(frozen=True)
class SolidDefinition:
    name: str
    vertices: np.ndarray
    faces: tuple[tuple[int, ...], ...] | None = None
    family: str = "Catálogo"
    note: str = ""
    validation_status: str = "stable"


def _as_array(points) -> np.ndarray:
    return np.array(points, dtype=float)


def _poly(n: int, radius: float = 1.0, z: float = 0.0, phase: float = 0.0) -> np.ndarray:
    return _as_array([
        [radius * np.cos(phase + 2*np.pi*i/n), radius * np.sin(phase + 2*np.pi*i/n), z]
        for i in range(n)
    ])


def _dedupe_points(points: Sequence[np.ndarray], decimals: int = 10) -> np.ndarray:
    out: list[np.ndarray] = []
    seen: set[tuple[float, float, float]] = set()
    for p in points:
        key = tuple(np.round(np.asarray(p, dtype=float), decimals=decimals).tolist())
        if key not in seen:
            seen.add(key)
            out.append(np.asarray(p, dtype=float))
    return np.array(out, dtype=float)


# -----------------------------------------------------------------------------
# Platônicos e prismas da v0.1
# -----------------------------------------------------------------------------

def tetrahedron_definition() -> SolidDefinition:
    vertices = _as_array([
        [1, 1, 1],
        [-1, -1, 1],
        [-1, 1, -1],
        [1, -1, -1],
    ])
    faces = ((0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 3, 2))
    return SolidDefinition("Tetraedro", vertices, faces, "Platônicos")


def cube_definition() -> SolidDefinition:
    vertices = _as_array([
        [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
        [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1],
    ])
    faces = (
        (0, 1, 2, 3), (4, 7, 6, 5),
        (0, 4, 5, 1), (1, 5, 6, 2),
        (2, 6, 7, 3), (3, 7, 4, 0),
    )
    return SolidDefinition("Cubo", vertices, faces, "Platônicos")


def octahedron_definition() -> SolidDefinition:
    vertices = _as_array([
        [1, 0, 0], [-1, 0, 0],
        [0, 1, 0], [0, -1, 0],
        [0, 0, 1], [0, 0, -1],
    ])
    faces = (
        (0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
        (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5),
    )
    return SolidDefinition("Octaedro", vertices, faces, "Platônicos")


def icosahedron_definition() -> SolidDefinition:
    vertices = []
    for s1 in (-1, 1):
        for s2 in (-1, 1):
            vertices.append([0, s1, s2 * PHI])
            vertices.append([s1, s2 * PHI, 0])
            vertices.append([s1 * PHI, 0, s2])
    return SolidDefinition("Icosaedro", _as_array(vertices), None, "Platônicos")


def dodecahedron_definition() -> SolidDefinition:
    vertices = []
    for i in (-1, 1):
        for j in (-1, 1):
            for k in (-1, 1):
                vertices.append([i, j, k])
    for i in (-1, 1):
        for j in (-1, 1):
            vertices.append([0, i * PHI, j / PHI])
            vertices.append([i / PHI, 0, j * PHI])
            vertices.append([i * PHI, j / PHI, 0])
    return SolidDefinition("Dodecaedro", _as_array(vertices), None, "Platônicos")


def prism_definition(n: int, name: str | None = None) -> SolidDefinition:
    h = 0.8
    bottom = _poly(n, 1.0, -h)
    top = _poly(n, 1.0, h)
    vertices = np.vstack([bottom, top])
    faces: list[tuple[int, ...]] = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    for i in range(n):
        faces.append((i, (i + 1) % n, n + (i + 1) % n, n + i))
    return SolidDefinition(name or f"Prisma {n}-gonal", vertices, tuple(faces), "Prismas")


# -----------------------------------------------------------------------------
# Famílias novas da v0.2
# -----------------------------------------------------------------------------

def antiprism_definition(n: int) -> SolidDefinition:
    h = 0.7
    bottom = _poly(n, 1.0, -h, 0.0)
    top = _poly(n, 1.0, h, np.pi / n)
    vertices = np.vstack([bottom, top])
    faces: list[tuple[int, ...]] = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    for i in range(n):
        faces.append((i, (i + 1) % n, n + i))
        faces.append(((i + 1) % n, n + (i + 1) % n, n + i))
    return SolidDefinition(f"Antiprisma {n}-gonal", vertices, tuple(faces), "Antiprismas")


def pyramid_definition(n: int, name: str | None = None, family: str = "Pirâmides") -> SolidDefinition:
    base = _poly(n, 1.05, -0.45, np.pi / n)
    apex = _as_array([[0, 0, 1.05]])
    vertices = np.vstack([base, apex])
    faces: list[tuple[int, ...]] = [tuple(reversed(range(n)))]
    for i in range(n):
        faces.append((i, (i + 1) % n, n))
    return SolidDefinition(name or f"Pirâmide {n}-gonal", vertices, tuple(faces), family)


def bipyramid_definition(n: int) -> SolidDefinition:
    ring = _poly(n, 1.0, 0.0, np.pi / n)
    vertices = np.vstack([ring, [[0, 0, 1.0], [0, 0, -1.0]]])
    top = n
    bottom = n + 1
    faces: list[tuple[int, ...]] = []
    for i in range(n):
        faces.append((i, (i + 1) % n, top))
        faces.append(((i + 1) % n, i, bottom))
    return SolidDefinition(f"Bipirâmide {n}-gonal", vertices, tuple(faces), "Bipirâmides")


def cupola_definition(n: int, name: str, family: str = "Johnson iniciais") -> SolidDefinition:
    top = _poly(n, 0.78, 0.75, np.pi / n)
    bottom = _poly(2*n, 1.28, -0.35, 0.0)
    vertices = np.vstack([top, bottom])
    b0 = n
    faces: list[tuple[int, ...]] = [tuple(range(n)), tuple(reversed(range(b0, b0 + 2*n)))]
    for i in range(n):
        t0 = i
        t1 = (i + 1) % n
        b_i = b0 + 2*i
        b_i1 = b0 + (2*i + 1) % (2*n)
        b_i2 = b0 + (2*i + 2) % (2*n)
        faces.append((t0, b_i, b_i1))
        faces.append((t0, t1, b_i2, b_i1))
    return SolidDefinition(name, vertices, tuple(faces), family, "Modelo Johnson didático: topologia de cúpula para visualização.")


def elongated_cupola_definition(n: int, name: str) -> SolidDefinition:
    top = _poly(n, 0.78, 0.95, np.pi / n)
    mid = _poly(2*n, 1.28, 0.0, 0.0)
    bottom = _poly(2*n, 1.28, -0.95, 0.0)
    vertices = np.vstack([top, mid, bottom])
    m0 = n
    b0 = n + 2*n
    faces: list[tuple[int, ...]] = [tuple(range(n)), tuple(reversed(range(b0, b0 + 2*n)))]
    for i in range(n):
        t0 = i
        t1 = (i + 1) % n
        m_i = m0 + 2*i
        m_i1 = m0 + (2*i + 1) % (2*n)
        m_i2 = m0 + (2*i + 2) % (2*n)
        faces.append((t0, m_i, m_i1))
        faces.append((t0, t1, m_i2, m_i1))
    for i in range(2*n):
        faces.append((m0 + i, m0 + (i + 1) % (2*n), b0 + (i + 1) % (2*n), b0 + i))
    return SolidDefinition(name, vertices, tuple(faces), "Johnson iniciais", "Cúpula alongada didática: cúpula + prisma.")


def rotunda_pentagonal_definition(name: str = "J6 Rotunda pentagonal") -> SolidDefinition:
    n = 5
    top = _poly(n, 0.82, 0.85, np.pi / n)
    bottom = _poly(2*n, 1.35, -0.35, 0.0)
    vertices = np.vstack([top, bottom])
    b0 = n
    faces: list[tuple[int, ...]] = [tuple(range(n)), tuple(reversed(range(b0, b0 + 2*n)))]
    for i in range(n):
        t0 = i
        t1 = (i + 1) % n
        b_i = b0 + 2*i
        b_i1 = b0 + (2*i + 1) % (2*n)
        b_i2 = b0 + (2*i + 2) % (2*n)
        b_i3 = b0 + (2*i + 3) % (2*n)
        faces.append((t0, b_i, b_i1))
        faces.append((t0, t1, b_i3, b_i2, b_i1))
    return SolidDefinition(name, vertices, tuple(faces), "Johnson experimentais", "EXPERIMENTAL: a auditoria v0.5.1 detectou malha não-manifold nesta parametrização didática da rotunda. Use apenas para visualização, não para volume formal.", "experimental")


def elongated_rotunda_pentagonal_definition() -> SolidDefinition:
    n = 5
    top = _poly(n, 0.82, 1.05, np.pi / n)
    mid = _poly(2*n, 1.35, 0.0, 0.0)
    bottom = _poly(2*n, 1.35, -1.0, 0.0)
    vertices = np.vstack([top, mid, bottom])
    m0 = n
    b0 = n + 2*n
    faces: list[tuple[int, ...]] = [tuple(range(n)), tuple(reversed(range(b0, b0 + 2*n)))]
    for i in range(n):
        t0 = i
        t1 = (i + 1) % n
        m_i = m0 + 2*i
        m_i1 = m0 + (2*i + 1) % (2*n)
        m_i2 = m0 + (2*i + 2) % (2*n)
        m_i3 = m0 + (2*i + 3) % (2*n)
        faces.append((t0, m_i, m_i1))
        faces.append((t0, t1, m_i3, m_i2, m_i1))
    for i in range(2*n):
        faces.append((m0 + i, m0 + (i + 1) % (2*n), b0 + (i + 1) % (2*n), b0 + i))
    return SolidDefinition("J10 Rotunda pentagonal alongada", vertices, tuple(faces), "Johnson experimentais", "EXPERIMENTAL: rotunda alongada baseada na J6 auditada como não-manifold. Use apenas para visualização, não para volume formal.", "experimental")


# -----------------------------------------------------------------------------
# Operações: truncamento, retificação e dualidade.
# -----------------------------------------------------------------------------

def _model_from_definition(definition: SolidDefinition):
    from .core import build_solid_from_definition
    return build_solid_from_definition(definition)


def rectified_definition(base: SolidDefinition, name: str, family: str = "Arquimedianos selecionados") -> SolidDefinition:
    model = _model_from_definition(base)
    points = []
    edges = set()
    for face in model.faces:
        ids = face.indices
        for a, b in zip(ids, ids[1:] + ids[:1]):
            edge = tuple(sorted((int(a), int(b))))
            if edge not in edges:
                edges.add(edge)
                points.append((model.vertices[edge[0]] + model.vertices[edge[1]]) / 2.0)
    return SolidDefinition(name, _dedupe_points(points), None, family, f"Retificação didática de {base.name}.")


def truncated_definition(base: SolidDefinition, name: str, t: float = 1.0/3.0, family: str = "Arquimedianos selecionados") -> SolidDefinition:
    model = _model_from_definition(base)
    points = []
    directed = set()
    for face in model.faces:
        ids = face.indices
        for a, b in zip(ids, ids[1:] + ids[:1]):
            a, b = int(a), int(b)
            if (a, b) not in directed:
                directed.add((a, b))
                points.append((1.0 - t) * model.vertices[a] + t * model.vertices[b])
            if (b, a) not in directed:
                directed.add((b, a))
                points.append((1.0 - t) * model.vertices[b] + t * model.vertices[a])
    return SolidDefinition(name, _dedupe_points(points), None, family, f"Truncamento didático de {base.name}.")


def dual_definition(source: SolidDefinition, name: str, family: str = "Catalan selecionados") -> SolidDefinition:
    model = _model_from_definition(source)
    points = []
    for face in model.faces:
        h = float(np.dot(face.normal, model.vertices[face.indices[0]] - model.center))
        if abs(h) < 1e-8:
            # fallback visual
            points.append(face.center)
        else:
            points.append(face.normal / h)
    return SolidDefinition(name, _as_array(points), None, family, f"Dual polar didático de {source.name}.")


# -----------------------------------------------------------------------------
# Catálogo
# -----------------------------------------------------------------------------

def _catalog_factories() -> dict[str, Callable[[], SolidDefinition]]:
    factories: dict[str, Callable[[], SolidDefinition]] = {}

    def add(fn: Callable[[], SolidDefinition]):
        # Preserve insertion order and avoid calling fn twice where possible.
        sample = fn()
        factories[sample.name] = fn

    # v0.1 base
    for fn in [
        tetrahedron_definition,
        cube_definition,
        octahedron_definition,
        icosahedron_definition,
        dodecahedron_definition,
        lambda: prism_definition(3, "Prisma triangular"),
        lambda: prism_definition(5, "Prisma pentagonal"),
    ]:
        add(fn)

    # Antiprismas
    for n in [3, 4, 5, 6, 8]:
        add(lambda n=n: antiprism_definition(n))

    # Pirâmides
    add(lambda: pyramid_definition(3, "Pirâmide triangular"))
    add(lambda: pyramid_definition(4, "Pirâmide quadrada"))
    add(lambda: pyramid_definition(5, "Pirâmide pentagonal"))
    add(lambda: pyramid_definition(6, "Pirâmide hexagonal"))

    # Bipirâmides
    for n in [3, 4, 5, 6, 8]:
        add(lambda n=n: bipyramid_definition(n))

    # Trapezoedros como duais de antiprismas
    for n in [3, 4, 5, 6]:
        add(lambda n=n: dual_definition(antiprism_definition(n), f"Trapezoedro {n}-gonal", "Trapezoedros"))

    # Arquimedianos selecionados, gerados por operações clássicas.
    add(lambda: rectified_definition(cube_definition(), "Cuboctaedro"))
    add(lambda: rectified_definition(dodecahedron_definition(), "Icosidodecaedro"))
    add(lambda: truncated_definition(tetrahedron_definition(), "Tetraedro truncado", 1/3))
    add(lambda: truncated_definition(cube_definition(), "Cubo truncado", 0.32))
    add(lambda: truncated_definition(octahedron_definition(), "Octaedro truncado", 1/3))
    add(lambda: truncated_definition(dodecahedron_definition(), "Dodecaedro truncado", 0.30))
    add(lambda: truncated_definition(icosahedron_definition(), "Icosaedro truncado", 1/3))

    # Catalan selecionados: duais dos Arquimedianos acima.
    add(lambda: dual_definition(rectified_definition(cube_definition(), "Cuboctaedro"), "Dodecaedro rômbico"))
    add(lambda: dual_definition(rectified_definition(dodecahedron_definition(), "Icosidodecaedro"), "Triacontaedro rômbico"))
    add(lambda: dual_definition(truncated_definition(tetrahedron_definition(), "Tetraedro truncado", 1/3), "Triakis tetraedro"))
    add(lambda: dual_definition(truncated_definition(cube_definition(), "Cubo truncado", 0.32), "Tetrakis hexaedro"))
    add(lambda: dual_definition(truncated_definition(octahedron_definition(), "Octaedro truncado", 1/3), "Triakis octaedro"))
    add(lambda: dual_definition(truncated_definition(icosahedron_definition(), "Icosaedro truncado", 1/3), "Pentakis dodecaedro"))

    # Johnson iniciais J1-J10.
    add(lambda: pyramid_definition(4, "J1 Pirâmide quadrada", "Johnson iniciais"))
    add(lambda: pyramid_definition(5, "J2 Pirâmide pentagonal", "Johnson iniciais"))
    add(lambda: cupola_definition(3, "J3 Cúpula triangular"))
    add(lambda: cupola_definition(4, "J4 Cúpula quadrada"))
    add(lambda: cupola_definition(5, "J5 Cúpula pentagonal"))
    add(lambda: rotunda_pentagonal_definition())
    add(lambda: elongated_cupola_definition(3, "J7 Cúpula triangular alongada"))
    add(lambda: elongated_cupola_definition(4, "J8 Cúpula quadrada alongada"))
    add(lambda: elongated_cupola_definition(5, "J9 Cúpula pentagonal alongada"))
    add(lambda: elongated_rotunda_pentagonal_definition())

    return factories


SOLID_DEFINITIONS: dict[str, Callable[[], SolidDefinition]] = _catalog_factories()
SOLID_NAMES: list[str] = list(SOLID_DEFINITIONS.keys())
EXPERIMENTAL_SOLID_NAMES: set[str] = {
    name for name, factory in SOLID_DEFINITIONS.items()
    if factory().validation_status == "experimental"
}


def is_experimental_solid(name: str) -> bool:
    return name in EXPERIMENTAL_SOLID_NAMES


def get_solid_definition(name: str) -> SolidDefinition:
    if name not in SOLID_DEFINITIONS:
        raise KeyError(f"Sólido não encontrado no catálogo: {name}")
    return SOLID_DEFINITIONS[name]()


@lru_cache(maxsize=1)
def catalog_metadata() -> dict[str, dict[str, str]]:
    data: dict[str, dict[str, str]] = {}
    for name, factory in SOLID_DEFINITIONS.items():
        d = factory()
        data[name] = {"family": d.family, "note": d.note, "validation_status": d.validation_status}
    return data


# Compatibilidade com v0.1: alguns testes/scripts antigos importavam SOLID_FACTORIES.
SOLID_FACTORIES: dict[str, Callable[[], np.ndarray]] = {
    name: (lambda name=name: get_solid_definition(name).vertices)
    for name in SOLID_NAMES
}
