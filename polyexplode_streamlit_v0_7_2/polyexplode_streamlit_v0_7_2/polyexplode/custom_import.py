from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from .core import EPS, build_solid, newell_normal, polygon_area
from .solids import SolidDefinition


@dataclass(frozen=True)
class ValidationMessage:
    level: str  # OK, INFO, AVISO, CRÍTICO
    item: str
    message: str

    def to_row(self) -> dict[str, str]:
        return {"Nível": self.level, "Item": self.item, "Mensagem": self.message}


@dataclass(frozen=True)
class MeshValidationReport:
    source_name: str
    format: str
    vertex_count: int
    face_count: int
    edge_count: int
    euler: int
    closed_manifold: bool
    convexity: str
    max_planarity_error: float
    unused_vertices: tuple[int, ...]
    messages: tuple[ValidationMessage, ...]

    @property
    def ok_to_build(self) -> bool:
        return not any(m.level == "CRÍTICO" for m in self.messages)

    @property
    def has_warnings(self) -> bool:
        return any(m.level == "AVISO" for m in self.messages)

    def to_jsonable(self) -> dict[str, Any]:
        data = asdict(self)
        data["messages"] = [m.to_row() for m in self.messages]
        data["ok_to_build"] = self.ok_to_build
        data["has_warnings"] = self.has_warnings
        return data

    def rows(self) -> list[dict[str, str]]:
        return [m.to_row() for m in self.messages]


@dataclass(frozen=True)
class ImportedSolid:
    definition: SolidDefinition
    report: MeshValidationReport


def _clean_off_lines(text: str) -> list[str]:
    cleaned: list[str] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            cleaned.append(line)
    return cleaned


def _coerce_vertices(vertices: Any) -> np.ndarray:
    arr = np.asarray(vertices, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError("A lista de vértices precisa ter formato N×3.")
    if not np.all(np.isfinite(arr)):
        raise ValueError("Há coordenadas não finitas nos vértices.")
    return arr


def _coerce_faces(faces: Any, vertex_count: int) -> tuple[tuple[int, ...], ...]:
    out: list[tuple[int, ...]] = []
    if not isinstance(faces, (list, tuple)):
        raise ValueError("A lista de faces precisa ser uma lista de listas de índices.")
    for idx, face in enumerate(faces, start=1):
        if not isinstance(face, (list, tuple)):
            raise ValueError(f"Face {idx} não é uma lista de índices.")
        try:
            ids = tuple(int(i) for i in face)
        except Exception as exc:
            raise ValueError(f"Face {idx} contém índice não inteiro.") from exc
        if len(ids) < 3:
            raise ValueError(f"Face {idx} tem menos de 3 vértices.")
        if len(set(ids)) != len(ids):
            raise ValueError(f"Face {idx} contém índices repetidos.")
        if min(ids) < 0 or max(ids) >= vertex_count:
            raise ValueError(f"Face {idx} referencia índice fora do intervalo 0..{vertex_count - 1}.")
        out.append(ids)
    if not out:
        raise ValueError("O arquivo não contém faces.")
    return tuple(out)


def parse_off(text: str, filename: str = "importado.off") -> SolidDefinition:
    lines = _clean_off_lines(text)
    if not lines:
        raise ValueError("Arquivo OFF vazio.")
    header = lines.pop(0).strip()
    if header.upper() != "OFF":
        raise ValueError("Formato OFF inválido: a primeira linha precisa ser OFF.")
    if not lines:
        raise ValueError("OFF sem linha de contagem de vértices/faces.")
    counts = lines.pop(0).split()
    if len(counts) < 2:
        raise ValueError("Linha de contagem OFF precisa informar pelo menos número de vértices e faces.")
    try:
        n_vertices = int(counts[0])
        n_faces = int(counts[1])
    except Exception as exc:
        raise ValueError("Contagens OFF inválidas.") from exc
    if n_vertices < 4:
        raise ValueError("OFF precisa ter ao menos 4 vértices para um sólido 3D.")
    if n_faces < 1:
        raise ValueError("OFF precisa declarar ao menos 1 face.")
    if len(lines) < n_vertices + n_faces:
        raise ValueError("OFF incompleto: há menos linhas que o declarado no cabeçalho.")

    vertices: list[list[float]] = []
    for i in range(n_vertices):
        parts = lines[i].split()
        if len(parts) < 3:
            raise ValueError(f"Linha de vértice {i + 1} tem menos de 3 coordenadas.")
        vertices.append([float(parts[0]), float(parts[1]), float(parts[2])])

    faces: list[tuple[int, ...]] = []
    for f_idx in range(n_faces):
        parts = lines[n_vertices + f_idx].split()
        if not parts:
            raise ValueError(f"Linha de face {f_idx + 1} vazia.")
        n = int(parts[0])
        if n < 3:
            raise ValueError(f"Face {f_idx + 1} declara menos de 3 vértices.")
        if len(parts) < n + 1:
            raise ValueError(f"Face {f_idx + 1} incompleta no OFF.")
        faces.append(tuple(int(p) for p in parts[1:n + 1]))

    v = _coerce_vertices(vertices)
    f = _coerce_faces(faces, len(v))
    stem = Path(filename).stem.replace("_", " ").replace("-", " ").strip() or "Sólido OFF importado"
    return SolidDefinition(stem.title(), v, f, "Importado", f"Importado de {filename} no formato OFF.")


def parse_json_solid(text: str, filename: str = "importado.json") -> SolidDefinition:
    try:
        data = json.loads(text)
    except Exception as exc:
        raise ValueError("JSON inválido.") from exc
    if not isinstance(data, dict):
        raise ValueError("JSON precisa ser um objeto com campos vertices e faces.")
    vertices = data.get("vertices")
    faces = data.get("faces")
    if vertices is None or faces is None:
        raise ValueError("JSON precisa conter os campos vertices e faces.")
    v = _coerce_vertices(vertices)
    f = _coerce_faces(faces, len(v))
    name = str(data.get("name") or data.get("nome") or Path(filename).stem or "Sólido JSON importado")
    family = str(data.get("family") or data.get("familia") or "Importado")
    note = str(data.get("note") or data.get("nota") or f"Importado de {filename} no formato JSON.")
    return SolidDefinition(name, v, f, family if family else "Importado", note)


def parse_uploaded_solid(text: str, filename: str) -> SolidDefinition:
    suffix = Path(filename).suffix.lower()
    if suffix == ".off":
        return parse_off(text, filename)
    if suffix == ".json":
        return parse_json_solid(text, filename)
    # fallback by content
    stripped = text.lstrip()
    if stripped.upper().startswith("OFF"):
        return parse_off(text, filename)
    if stripped.startswith("{"):
        return parse_json_solid(text, filename)
    raise ValueError("Formato não reconhecido. Use .off ou .json.")


def _edge_counts(faces: Sequence[Sequence[int]]) -> dict[tuple[int, int], int]:
    counts: dict[tuple[int, int], int] = {}
    for face in faces:
        ids = list(face)
        for a, b in zip(ids, ids[1:] + ids[:1]):
            edge = tuple(sorted((int(a), int(b))))
            counts[edge] = counts.get(edge, 0) + 1
    return counts


def _referenced_vertices(faces: Sequence[Sequence[int]]) -> set[int]:
    refs: set[int] = set()
    for face in faces:
        refs.update(int(i) for i in face)
    return refs


def _face_planarity_error(vertices: np.ndarray, face: Sequence[int]) -> float:
    pts = vertices[list(face)]
    if len(pts) <= 3:
        return 0.0
    normal = newell_normal(pts)
    d = float(np.dot(normal, pts[0]))
    distances = np.abs(pts @ normal - d)
    scale = max(1.0, float(np.max(np.linalg.norm(vertices - vertices.mean(axis=0), axis=1))))
    return float(np.max(distances) / scale)


def _detect_convexity(vertices: np.ndarray, faces: Sequence[Sequence[int]], tol: float = 1e-6) -> str:
    if len(vertices) < 4 or len(faces) < 4:
        return "indeterminado"
    supporting = 0
    non_supporting = 0
    for face in faces:
        pts = vertices[list(face)]
        try:
            normal = newell_normal(pts)
        except ValueError:
            return "indeterminado"
        d = float(np.dot(normal, pts[0]))
        signed = vertices @ normal - d
        # Ignore face vertices themselves.
        mask = np.ones(len(vertices), dtype=bool)
        mask[list(face)] = False
        other = signed[mask]
        if len(other) == 0:
            supporting += 1
            continue
        if np.all(other <= tol) or np.all(other >= -tol):
            supporting += 1
        else:
            non_supporting += 1
    if non_supporting == 0 and supporting == len(faces):
        return "convexo provável"
    return "não convexo ou faces internas/cruzadas"


def validate_definition(definition: SolidDefinition, fmt: str | None = None) -> MeshValidationReport:
    messages: list[ValidationMessage] = []
    v = np.asarray(definition.vertices, dtype=float)
    faces = tuple(tuple(int(i) for i in face) for face in (definition.faces or ()))
    fmt = fmt or Path(definition.name).suffix.lower().lstrip(".") or "desconhecido"

    def add(level: str, item: str, message: str) -> None:
        messages.append(ValidationMessage(level, item, message))

    if v.ndim != 2 or v.shape[1] != 3:
        add("CRÍTICO", "vértices", "A matriz de vértices não tem formato N×3.")
        return MeshValidationReport(definition.name, fmt, 0, 0, 0, 0, False, "indeterminado", 0.0, tuple(), tuple(messages))
    if not np.all(np.isfinite(v)):
        add("CRÍTICO", "vértices", "Há coordenadas não finitas.")
    if len(v) < 4:
        add("CRÍTICO", "vértices", "Um sólido 3D simples precisa de ao menos 4 vértices.")
    if len(faces) < 4:
        add("AVISO", "faces", "Há menos de 4 faces; provavelmente é uma malha aberta ou incompleta.")

    valid_faces: list[tuple[int, ...]] = []
    for idx, face in enumerate(faces, start=1):
        if len(face) < 3:
            add("CRÍTICO", f"face {idx}", "Face com menos de 3 vértices.")
            continue
        if len(set(face)) != len(face):
            add("CRÍTICO", f"face {idx}", "Face com índice repetido.")
            continue
        if min(face) < 0 or max(face) >= len(v):
            add("CRÍTICO", f"face {idx}", "Face referencia vértice fora do intervalo.")
            continue
        try:
            area = polygon_area(v[list(face)])
            _ = newell_normal(v[list(face)])
        except Exception:
            add("CRÍTICO", f"face {idx}", "Face degenerada ou colinear.")
            continue
        if area <= EPS:
            add("CRÍTICO", f"face {idx}", "Área da face é zero ou praticamente zero.")
            continue
        valid_faces.append(face)

    edges = _edge_counts(valid_faces)
    euler = int(len(v) - len(edges) + len(valid_faces)) if len(v) else 0
    unused = tuple(sorted(set(range(len(v))) - _referenced_vertices(valid_faces)))
    max_planarity = 0.0
    if valid_faces:
        max_planarity = max(_face_planarity_error(v, face) for face in valid_faces)

    if unused:
        add("AVISO", "vértices não usados", f"Há {len(unused)} vértice(s) que não aparecem em nenhuma face.")

    non_two = {edge: count for edge, count in edges.items() if count != 2}
    closed = len(edges) > 0 and not non_two
    if closed:
        add("OK", "malha", "Todas as arestas aparecem em exatamente duas faces: malha fechada provável.")
    else:
        boundary = sum(1 for c in edges.values() if c == 1)
        nonmanifold = sum(1 for c in edges.values() if c > 2)
        add("AVISO", "malha", f"A malha pode não ser fechada/manifold: {boundary} aresta(s) de borda e {nonmanifold} aresta(s) não-manifold.")

    if euler == 2:
        add("OK", "Euler", "V - E + F = 2, compatível com poliedro convexo/esfera topológica simples.")
    else:
        add("AVISO", "Euler", f"V - E + F = {euler}. Isso pode indicar buraco, componente múltiplo, face faltante ou malha problemática.")

    if max_planarity <= 1e-5:
        add("OK", "planaridade", f"Erro máximo de planaridade relativo ≈ {max_planarity:.2e}.")
    else:
        add("AVISO", "planaridade", f"Algumas faces podem não ser planares. Erro relativo máximo ≈ {max_planarity:.2e}.")

    convexity = _detect_convexity(v, valid_faces)
    if convexity == "convexo provável":
        add("OK", "convexidade", "Todas as faces se comportam como planos de suporte: convexidade provável.")
    else:
        add("AVISO", "convexidade", "O sólido não parece convexo, ou contém faces internas/cruzadas. A explosão continua visual, mas o volume pode ser interpretado com cautela.")

    if not any(m.level == "CRÍTICO" for m in messages):
        try:
            model = build_solid(definition.name, v, valid_faces, normalize=True, family=definition.family, note=definition.note)
            if model.volume <= EPS:
                add("CRÍTICO", "volume", "Volume calculado nulo ou negativo.")
            else:
                add("OK", "construção", "O PolyExplode conseguiu montar o sólido importado.")
        except Exception as exc:
            add("CRÍTICO", "construção", f"Falha ao montar o sólido: {exc}")

    return MeshValidationReport(
        source_name=definition.name,
        format=fmt,
        vertex_count=int(len(v)),
        face_count=int(len(valid_faces)),
        edge_count=int(len(edges)),
        euler=euler,
        closed_manifold=closed,
        convexity=convexity,
        max_planarity_error=float(max_planarity),
        unused_vertices=unused,
        messages=tuple(messages),
    )


def import_uploaded_solid(text: str, filename: str) -> ImportedSolid:
    definition = parse_uploaded_solid(text, filename)
    fmt = Path(filename).suffix.lower().lstrip(".") or ("off" if text.lstrip().upper().startswith("OFF") else "json")
    report = validate_definition(definition, fmt=fmt)
    if not report.ok_to_build:
        return ImportedSolid(definition, report)
    note_parts = [definition.note, f"Validação de importação: {report.convexity}; Euler={report.euler}; malha fechada={report.closed_manifold}."]
    definition = SolidDefinition(
        definition.name,
        definition.vertices,
        definition.faces,
        "Importado",
        " ".join(part for part in note_parts if part),
    )
    return ImportedSolid(definition, report)


def validation_rows(report: MeshValidationReport) -> list[dict[str, str]]:
    return report.rows()


def example_off_cube() -> str:
    return """OFF
8 6 12
-1 -1 -1
1 -1 -1
1 1 -1
-1 1 -1
-1 -1 1
1 -1 1
1 1 1
-1 1 1
4 0 1 2 3
4 4 7 6 5
4 0 4 5 1
4 1 5 6 2
4 2 6 7 3
4 3 7 4 0
"""


def example_json_tetrahedron() -> str:
    return json.dumps(
        {
            "name": "Tetraedro importado",
            "vertices": [[1, 1, 1], [-1, -1, 1], [-1, 1, -1], [1, -1, -1]],
            "faces": [[0, 1, 2], [0, 3, 1], [0, 2, 3], [1, 3, 2]],
        },
        ensure_ascii=False,
        indent=2,
    )
