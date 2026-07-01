from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .core import SolidModel, Face, face_type_name

DECOMPOSITION_MODES = [
    "Pirâmides face-centro",
    "Faces",
    "Componentes",
    "Camadas",
    "Vértices/arestas/faces",
]

MODE_HELP = {
    "Pirâmides face-centro": "Cada face gera uma pirâmide cujo ápice é o centro do sólido. É o modo volumétrico principal.",
    "Faces": "As faces são afastadas como placas poligonais, sem desenhar as faces laterais das pirâmides.",
    "Componentes": "Separa componentes conectados da malha. No catálogo atual quase todos os sólidos têm um único componente.",
    "Camadas": "Agrupa faces por posição inferior/equatorial/superior e aplica afastamentos escalonados.",
    "Vértices/arestas/faces": "Separa a estrutura topológica: vértices como pontos, arestas como segmentos e faces como placas translúcidas.",
}


@dataclass(frozen=True)
class DecompositionInfo:
    mode: str
    piece_count: int
    groups: tuple[str, ...]
    description: str
    warning: str = ""

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "piece_count": self.piece_count,
            "groups": list(self.groups),
            "description": self.description,
            "warning": self.warning,
        }


def edge_pairs(model: SolidModel) -> list[tuple[int, int]]:
    edges: set[tuple[int, int]] = set()
    for face in model.faces:
        ids = [int(i) for i in face.indices]
        for a, b in zip(ids, ids[1:] + ids[:1]):
            edges.add(tuple(sorted((int(a), int(b)))))
    return sorted(edges)


def face_adjacency(model: SolidModel) -> dict[int, set[int]]:
    edge_to_faces: dict[tuple[int, int], list[int]] = {}
    for face_index, face in enumerate(model.faces):
        ids = [int(i) for i in face.indices]
        for a, b in zip(ids, ids[1:] + ids[:1]):
            edge_to_faces.setdefault(tuple(sorted((int(a), int(b)))), []).append(face_index)
    adjacency = {i: set() for i in range(len(model.faces))}
    for incident in edge_to_faces.values():
        for i in incident:
            for j in incident:
                if i != j:
                    adjacency[i].add(j)
    return adjacency


def connected_face_components(model: SolidModel) -> list[list[int]]:
    adjacency = face_adjacency(model)
    unseen = set(range(len(model.faces)))
    components: list[list[int]] = []
    while unseen:
        seed = min(unseen)
        stack = [seed]
        unseen.remove(seed)
        comp: list[int] = []
        while stack:
            current = stack.pop()
            comp.append(current)
            for nxt in sorted(adjacency[current]):
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)
        components.append(sorted(comp))
    return components


def face_layer(model: SolidModel, face: Face) -> str:
    centers = np.array([f.center for f in model.faces], dtype=float)
    zmin = float(np.min(centers[:, 2]))
    zmax = float(np.max(centers[:, 2]))
    if abs(zmax - zmin) < 1e-9:
        return "Camada equatorial"
    t = (float(face.center[2]) - zmin) / (zmax - zmin)
    if t < 1 / 3:
        return "Camada inferior"
    if t > 2 / 3:
        return "Camada superior"
    return "Camada equatorial"


def layer_multiplier(layer: str) -> float:
    return {
        "Camada inferior": 0.65,
        "Camada equatorial": 1.00,
        "Camada superior": 1.35,
    }.get(layer, 1.0)


def decomposition_info(model: SolidModel, mode: str) -> DecompositionInfo:
    if mode not in DECOMPOSITION_MODES:
        mode = "Pirâmides face-centro"
    if mode == "Pirâmides face-centro":
        return DecompositionInfo(
            mode=mode,
            piece_count=len(model.faces),
            groups=tuple(face_type_name(sides) for sides in sorted(model.face_histogram)),
            description=f"O sólido é decomposto em {len(model.faces)} pirâmides, uma por face, todas com ápice no centro.",
        )
    if mode == "Faces":
        return DecompositionInfo(
            mode=mode,
            piece_count=len(model.faces),
            groups=tuple(face_type_name(sides) for sides in sorted(model.face_histogram)),
            description=f"O sólido é separado em {len(model.faces)} placas de face, útil para estudar a casca poligonal.",
        )
    if mode == "Componentes":
        components = connected_face_components(model)
        warning = "" if len(components) > 1 else "O catálogo atual contém uma única componente conectada para este sólido; a separação por componentes será visualmente discreta."
        return DecompositionInfo(
            mode=mode,
            piece_count=len(components),
            groups=tuple(f"Componente {i + 1}: {len(comp)} faces" for i, comp in enumerate(components)),
            description=f"A malha foi particionada em {len(components)} componente(s) conectada(s) por adjacência de arestas.",
            warning=warning,
        )
    if mode == "Camadas":
        layers = [face_layer(model, face) for face in model.faces]
        groups = tuple(f"{label}: {layers.count(label)} faces" for label in ["Camada inferior", "Camada equatorial", "Camada superior"] if label in layers)
        return DecompositionInfo(
            mode=mode,
            piece_count=len(model.faces),
            groups=groups,
            description="As faces são organizadas em camadas inferior/equatorial/superior e explodem com intensidades diferentes.",
        )
    edges = edge_pairs(model)
    return DecompositionInfo(
        mode=mode,
        piece_count=len(model.vertices) + len(edges) + len(model.faces),
        groups=(f"Vértices: {len(model.vertices)}", f"Arestas: {len(edges)}", f"Faces: {len(model.faces)}"),
        description="A estrutura topológica V/E/F é separada para evidenciar vértices, arestas e faces como entidades distintas.",
    )


def decomposition_rows(model: SolidModel, mode: str) -> list[dict[str, Any]]:
    info = decomposition_info(model, mode)
    if mode == "Componentes":
        return [
            {"Grupo": f"Componente {i + 1}", "Faces": len(comp), "Descrição": "submalha conectada por arestas"}
            for i, comp in enumerate(connected_face_components(model))
        ]
    if mode == "Camadas":
        rows: list[dict[str, Any]] = []
        for label in ["Camada inferior", "Camada equatorial", "Camada superior"]:
            faces = [idx + 1 for idx, face in enumerate(model.faces) if face_layer(model, face) == label]
            if faces:
                rows.append({"Grupo": label, "Faces": len(faces), "Multiplicador": layer_multiplier(label), "Índices": ", ".join(map(str, faces[:24])) + ("..." if len(faces) > 24 else "")})
        return rows
    if mode == "Vértices/arestas/faces":
        return [
            {"Entidade": "Vértices", "Quantidade": len(model.vertices), "Função didática": "pontos da malha"},
            {"Entidade": "Arestas", "Quantidade": len(edge_pairs(model)), "Função didática": "conexões entre vértices"},
            {"Entidade": "Faces", "Quantidade": len(model.faces), "Função didática": "polígonos que fecham a superfície"},
        ]
    return [
        {"Peça": idx + 1, "Base/face": face_type_name(face.sides), "Área": float(face.area), "Altura": float(face.distance_to_center), "Volume piramidal": float(face.area * face.distance_to_center / 3.0)}
        for idx, face in enumerate(model.faces)
    ]
