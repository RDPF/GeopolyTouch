from __future__ import annotations

from dataclasses import dataclass, asdict
from itertools import combinations
import json
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np


EPS = 1e-8


@dataclass
class Face:
    indices: list[int]
    normal: np.ndarray
    center: np.ndarray
    area: float
    distance_to_center: float

    @property
    def sides(self) -> int:
        return len(self.indices)

    def to_jsonable(self) -> dict:
        data = asdict(self)
        data["normal"] = self.normal.tolist()
        data["center"] = self.center.tolist()
        data["indices"] = [int(i) for i in self.indices]
        data["sides"] = int(self.sides)
        return data




@dataclass
class DualGraph:
    """Visual graph of the polyhedral dual using face centers.

    Vertices of the dual are centers of the original faces. Edges connect
    centers of adjacent faces, i.e. faces sharing one original edge.
    """
    vertices: np.ndarray
    edges: list[tuple[int, int]]

    def to_jsonable(self) -> dict:
        return {
            "vertices": self.vertices.tolist(),
            "edges": [[int(a), int(b)] for a, b in self.edges],
            "vertex_count": int(len(self.vertices)),
            "edge_count": int(len(self.edges)),
        }


@dataclass
class SolidModel:
    name: str
    vertices: np.ndarray
    faces: list[Face]
    center: np.ndarray
    radius: float
    volume: float
    family: str = "Catálogo"
    note: str = ""
    construction: str = "pirâmides face-centro"

    @property
    def edge_count(self) -> int:
        edges = set()
        for face in self.faces:
            ids = face.indices
            for a, b in zip(ids, ids[1:] + ids[:1]):
                edges.add(tuple(sorted((int(a), int(b)))))
        return len(edges)

    @property
    def euler_characteristic(self) -> int:
        return len(self.vertices) - self.edge_count + len(self.faces)

    @property
    def face_histogram(self) -> dict[int, int]:
        hist: dict[int, int] = {}
        for face in self.faces:
            hist[face.sides] = hist.get(face.sides, 0) + 1
        return dict(sorted(hist.items()))

    def summary(self) -> dict:
        return {
            "name": self.name,
            "family": self.family,
            "vertices": int(len(self.vertices)),
            "edges": int(self.edge_count),
            "faces": int(len(self.faces)),
            "euler": int(self.euler_characteristic),
            "face_histogram": {str(k): int(v) for k, v in self.face_histogram.items()},
            "volume_by_face_pyramids": float(self.volume),
            "radius": float(self.radius),
            "note": self.note,
        }


def normalize_vertices(vertices: np.ndarray, target_radius: float = 1.55) -> np.ndarray:
    v = np.array(vertices, dtype=float)
    center = v.mean(axis=0)
    v = v - center
    radius = np.max(np.linalg.norm(v, axis=1))
    if radius <= EPS:
        raise ValueError("Conjunto de vértices degenerado.")
    return v * (target_radius / radius)


def polygon_area(points: np.ndarray) -> float:
    if len(points) < 3:
        return 0.0
    area_vector = np.zeros(3)
    for a, b in zip(points, np.roll(points, -1, axis=0)):
        area_vector += np.cross(a, b)
    return 0.5 * float(np.linalg.norm(area_vector))


def newell_normal(points: np.ndarray) -> np.ndarray:
    n = np.zeros(3, dtype=float)
    for a, b in zip(points, np.roll(points, -1, axis=0)):
        n += np.cross(a, b)
    norm = np.linalg.norm(n)
    if norm <= EPS:
        # fallback: first non-collinear triple
        for i, j, k in combinations(range(len(points)), 3):
            cand = np.cross(points[j] - points[i], points[k] - points[i])
            cand_norm = np.linalg.norm(cand)
            if cand_norm > EPS:
                return cand / cand_norm
        raise ValueError("Face degenerada: não há normal bem definida.")
    return n / norm


def order_face_indices(vertices: np.ndarray, indices: Iterable[int], normal: np.ndarray) -> list[int]:
    ids = list(indices)
    pts = vertices[ids]
    center = pts.mean(axis=0)
    n_norm = np.linalg.norm(normal)
    if n_norm <= EPS:
        raise ValueError("Normal degenerada ao ordenar face.")
    n = normal / n_norm

    u = pts[0] - center
    u_norm = np.linalg.norm(u)
    if u_norm <= EPS:
        raise ValueError("Face degenerada ao ordenar vértices.")
    u = u / u_norm
    v = np.cross(n, u)

    rel = pts - center
    angles = np.arctan2(rel @ v, rel @ u)
    ordered_local = np.argsort(angles)
    ordered = [ids[i] for i in ordered_local]

    ordered_pts = vertices[ordered]
    area_vec = np.zeros(3)
    for a, b in zip(ordered_pts, np.roll(ordered_pts, -1, axis=0)):
        area_vec += np.cross(a - center, b - center)
    if np.dot(area_vec, n) < 0:
        ordered.reverse()
    return ordered


def make_explicit_face(vertices: np.ndarray, indices: Sequence[int], solid_center: np.ndarray) -> Face:
    ordered = [int(i) for i in indices]
    if len(set(ordered)) != len(ordered):
        raise ValueError(f"Face com índices repetidos: {ordered}")
    pts = vertices[ordered]
    face_center = pts.mean(axis=0)
    normal = newell_normal(pts)
    if np.dot(normal, face_center - solid_center) < 0:
        ordered = list(reversed(ordered))
        pts = vertices[ordered]
        normal = newell_normal(pts)
        face_center = pts.mean(axis=0)
    area = polygon_area(pts)
    dist = abs(float(np.dot(normal, pts[0] - solid_center)))
    return Face(indices=ordered, normal=normal, center=face_center, area=area, distance_to_center=dist)


def find_convex_faces(vertices: np.ndarray, tol: float = 1e-7) -> list[Face]:
    """Find supporting planes and polygonal faces of a small convex polyhedron.

    This intentionally avoids scipy so the PC prototype has only numpy+matplotlib
    as external dependencies. It is meant for small convex educational solids.
    """
    v = np.array(vertices, dtype=float)
    n_vertices = len(v)
    center = v.mean(axis=0)
    seen: set[frozenset[int]] = set()
    faces: list[Face] = []

    for i, j, k in combinations(range(n_vertices), 3):
        p0, p1, p2 = v[i], v[j], v[k]
        normal = np.cross(p1 - p0, p2 - p0)
        norm = np.linalg.norm(normal)
        if norm <= tol:
            continue
        normal = normal / norm
        signed = (v - p0) @ normal

        if np.all(signed >= -tol) or np.all(signed <= tol):
            ids = frozenset(np.where(np.abs(signed) <= tol)[0].tolist())
            if len(ids) < 3 or ids in seen:
                continue
            seen.add(ids)

            face_center = v[list(ids)].mean(axis=0)
            if np.dot(normal, face_center - center) < 0:
                normal = -normal
            ordered = order_face_indices(v, ids, normal)
            pts = v[ordered]
            area = polygon_area(pts)
            dist = abs(float(np.dot(normal, pts[0] - center)))
            faces.append(Face(
                indices=ordered,
                normal=normal,
                center=face_center,
                area=area,
                distance_to_center=dist,
            ))

    faces.sort(key=lambda f: (round(float(f.center[2]), 6), round(float(f.center[1]), 6), round(float(f.center[0]), 6)))
    return faces


def build_solid(
    name: str,
    vertices: np.ndarray,
    faces: Sequence[Sequence[int]] | None = None,
    normalize: bool = True,
    family: str = "Catálogo",
    note: str = "",
    construction: str = "pirâmides face-centro",
) -> SolidModel:
    v = normalize_vertices(vertices) if normalize else np.array(vertices, dtype=float)
    center = v.mean(axis=0)
    if faces is None:
        face_objects = find_convex_faces(v)
    else:
        face_objects = [make_explicit_face(v, face, center) for face in faces]
    if not face_objects:
        raise ValueError(f"Não foi possível encontrar faces para {name}.")
    radius = float(np.max(np.linalg.norm(v - center, axis=1)))
    volume = sum(face.area * face.distance_to_center / 3.0 for face in face_objects)
    return SolidModel(
        name=name,
        vertices=v,
        faces=face_objects,
        center=center,
        radius=radius,
        volume=float(volume),
        family=family,
        note=note,
        construction=construction,
    )


def build_solid_from_definition(definition, normalize: bool = True) -> SolidModel:
    """Build a SolidModel from a SolidDefinition-like object."""
    return build_solid(
        name=definition.name,
        vertices=definition.vertices,
        faces=definition.faces,
        normalize=normalize,
        family=getattr(definition, "family", "Catálogo"),
        note=getattr(definition, "note", ""),
    )


def exploded_piece_vertices(model: SolidModel, face: Face, explosion: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return shifted base, shifted apex and shift vector for a face pyramid."""
    shift = face.normal * float(explosion) * model.radius
    base = model.vertices[face.indices] + shift
    apex = model.center + shift
    return base, apex, shift


def face_type_name(sides: int) -> str:
    """Portuguese UI label for a face class by number of sides."""
    names = {
        3: "Triângulos",
        4: "Quadriláteros",
        5: "Pentágonos",
        6: "Hexágonos",
        8: "Octógonos",
        10: "Decágonos",
    }
    return names.get(int(sides), f"{int(sides)}-gonos")


def face_filter_options(model: SolidModel) -> list[str]:
    """Return the available face-type filters for the current solid."""
    return ["Todas"] + [face_type_name(sides) for sides in sorted(model.face_histogram)]


def face_matches_filter(face: Face, filter_name: str) -> bool:
    """Whether a face should receive the explosion factor under a UI filter."""
    return filter_name == "Todas" or filter_name == face_type_name(face.sides)


def build_dual_graph(
    model: SolidModel,
    outward_scale: float = 1.055,
    *,
    explosion: float = 0.0,
    face_filter: str = "Todas",
    follow_explosion: bool = False,
    progress: float = 1.0,
) -> DualGraph:
    """Build a visual dual graph from face centers and face adjacency.

    This is deliberately a visual/combinatorial dual: every original face
    contributes one dual vertex, and every original edge contributes one dual
    edge connecting the two adjacent faces. It is ideal for showing the dual
    emerging from the exploded solid without requiring exact Catalan metrics.

    When ``follow_explosion`` is true, each dual vertex receives the same
    displacement as the exploded face/pyramid that generated it. This keeps
    the visual relation "original face -> dual vertex" legible even at high
    explosion factors. The displacement respects ``face_filter``: faces not
    currently exploded keep their fixed dual vertex position.
    """
    centers = np.array([face.center for face in model.faces], dtype=float)
    vertices = model.center + (centers - model.center) * float(outward_scale)
    if follow_explosion and len(model.faces):
        dual_progress = max(0.0, min(1.0, float(progress)))
        shifts = []
        for face in model.faces:
            local_explosion = float(explosion) if face_matches_filter(face, face_filter) else 0.0
            shifts.append(face.normal * local_explosion * model.radius * dual_progress)
        vertices = vertices + np.array(shifts, dtype=float)
    edge_to_faces: dict[tuple[int, int], list[int]] = {}
    for face_index, face in enumerate(model.faces):
        ids = [int(i) for i in face.indices]
        for a, b in zip(ids, ids[1:] + ids[:1]):
            edge = tuple(sorted((int(a), int(b))))
            edge_to_faces.setdefault(edge, []).append(int(face_index))

    edges: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for adjacent_faces in edge_to_faces.values():
        unique_faces = []
        for face_index in adjacent_faces:
            if face_index not in unique_faces:
                unique_faces.append(face_index)
        if len(unique_faces) < 2:
            continue
        # In a clean manifold edge there are exactly two incident faces.
        # For the didactic Johnson-layer models, an edge may have more than
        # two incident faces; choose the first two so the visual dual remains
        # stable and keeps one visual dual edge per original edge.
        pair = tuple(sorted((unique_faces[0], unique_faces[1])))
        if pair not in seen:
            seen.add(pair)
            edges.append((int(pair[0]), int(pair[1])))
    return DualGraph(vertices=vertices, edges=edges)


def export_manifest(model: SolidModel, path: str | Path) -> Path:
    path = Path(path)
    dual = build_dual_graph(model)
    data = {
        "project": "PolyExplode Lab",
        "format_version": "streamlit-0.6",
        "solid": model.summary(),
        "face_type_filters": face_filter_options(model),
        "dual_graph": dual.to_jsonable(),
        "faces": [face.to_jsonable() for face in model.faces],
        "notes": [
            "Decomposição por pirâmides face-centro.",
            "Volume total calculado como soma área(face)*distância(centro, plano)/3.",
            "Streamlit v0.3 acrescenta anatomia didática, tabela de peças, modo professor, relatório HTML e Dual Explorer.",
            "Streamlit v0.4 acrescenta importação OFF/JSON, validação de malha, convexidade e avisos para sólidos problemáticos.",
            "Streamlit v0.5.2 alinha o overlay do dual à explosão das faces quando solicitado.",
            "Streamlit v0.6 acrescenta diagnósticos matemáticos: orientação, normais externas, planaridade, manifoldness e convexidade.",
            "O dual visual usa centros de faces e adjacência combinatória; não substitui certificação métrica de sólidos de Catalan.",
            "O projeto continua sem STL nesta linha de desenvolvimento.",
        ],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
