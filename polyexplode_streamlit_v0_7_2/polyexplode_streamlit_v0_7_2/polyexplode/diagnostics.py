from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Sequence

import numpy as np

from .core import EPS, Face, SolidModel, build_solid_from_definition
from .custom_import import MeshValidationReport, validate_definition
from .solids import EXPERIMENTAL_SOLID_NAMES, SOLID_NAMES, SolidDefinition, get_solid_definition

PLANARITY_TOL = 1e-5
ORIENTATION_TOL = 1e-8
CONVEXITY_TOL = 1e-6


@dataclass(frozen=True)
class DiagnosticMessage:
    level: str  # OK, INFO, AVISO, CRÍTICO
    item: str
    message: str

    def to_row(self) -> dict[str, str]:
        return {"Nível": self.level, "Item": self.item, "Mensagem": self.message}


@dataclass(frozen=True)
class TechnicalDiagnosticReport:
    name: str
    family: str
    status: str
    vertex_count: int
    edge_count: int
    face_count: int
    euler: int
    outward_normals_ok: bool
    min_orientation_dot: float
    max_planarity_error: float
    planar_faces_ok: bool
    closed_manifold: bool
    boundary_edge_count: int
    nonmanifold_edge_count: int
    convexity: str
    convexity_violations: int
    max_convexity_violation: float
    messages: tuple[DiagnosticMessage, ...]

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    @property
    def has_warnings(self) -> bool:
        return self.status in {"aviso", "experimental"}

    def to_jsonable(self) -> dict[str, Any]:
        data = asdict(self)
        data["messages"] = [m.to_row() for m in self.messages]
        data["ok"] = self.ok
        data["has_warnings"] = self.has_warnings
        return data

    def to_summary_row(self) -> dict[str, Any]:
        return {
            "Sólido": self.name,
            "Família": self.family,
            "Status": self.status,
            "V": self.vertex_count,
            "E": self.edge_count,
            "F": self.face_count,
            "χ": self.euler,
            "Normais externas": self.outward_normals_ok,
            "Planaridade máx.": self.max_planarity_error,
            "Manifold fechado": self.closed_manifold,
            "Arestas de borda": self.boundary_edge_count,
            "Arestas não-manifold": self.nonmanifold_edge_count,
            "Convexidade": self.convexity,
            "Violações convexidade": self.convexity_violations,
        }

    def message_rows(self) -> list[dict[str, str]]:
        return [m.to_row() for m in self.messages]


@dataclass(frozen=True)
class InternalCatalogValidation:
    name: str
    status: str
    closed_manifold: bool
    euler: int
    max_planarity_error: float
    warning_count: int
    critical_count: int
    message: str

    def to_row(self) -> dict[str, Any]:
        return {
            "Sólido": self.name,
            "Status": self.status,
            "Malha fechada/manifold": self.closed_manifold,
            "χ": self.euler,
            "Planaridade máx.": self.max_planarity_error,
            "Avisos": self.warning_count,
            "Críticos": self.critical_count,
            "Mensagem": self.message,
        }


def definition_from_built_model(model: SolidModel) -> SolidDefinition:
    """Convert a built model back to an explicit-face definition for validation.

    Many catalog definitions intentionally store only vertices and rely on
    convex-face discovery. Validating those raw definitions would see no faces.
    This helper validates the actual mesh the application renders.
    """
    return SolidDefinition(
        name=model.name,
        vertices=model.vertices,
        faces=tuple(tuple(face.indices) for face in model.faces),
        family=model.family,
        note=model.note,
        validation_status="experimental" if model.name in EXPERIMENTAL_SOLID_NAMES else "stable",
    )


def validate_built_model(model: SolidModel) -> MeshValidationReport:
    return validate_definition(definition_from_built_model(model), fmt="internal-built")


def edge_multiplicities(model: SolidModel) -> dict[tuple[int, int], int]:
    counts: dict[tuple[int, int], int] = {}
    for face in model.faces:
        ids = [int(i) for i in face.indices]
        for a, b in zip(ids, ids[1:] + ids[:1]):
            edge = tuple(sorted((int(a), int(b))))
            counts[edge] = counts.get(edge, 0) + 1
    return counts


def face_planarity_error(model: SolidModel, face: Face) -> float:
    pts = model.vertices[face.indices]
    if len(pts) <= 3:
        return 0.0
    d = float(np.dot(face.normal, pts[0]))
    distances = np.abs(pts @ face.normal - d)
    scale = max(1.0, float(model.radius))
    return float(np.max(distances) / scale)


def face_orientation_dot(model: SolidModel, face: Face) -> float:
    return float(np.dot(face.normal, face.center - model.center))


def face_diagnostic_rows(model: SolidModel) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, face in enumerate(model.faces, start=1):
        orient = face_orientation_dot(model, face)
        planarity = face_planarity_error(model, face)
        rows.append({
            "Face": idx,
            "Lados": face.sides,
            "Normal externa?": orient > ORIENTATION_TOL,
            "Dot normal·(centro_face-centro)": orient,
            "Planaridade relativa": planarity,
            "Área": float(face.area),
            "Altura ao centro": float(face.distance_to_center),
        })
    return rows


def edge_diagnostic_rows(model: SolidModel, max_rows: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (a, b), count in sorted(edge_multiplicities(model).items()):
        if count == 2:
            status = "OK"
        elif count == 1:
            status = "BORDA"
        else:
            status = "NÃO-MANIFOLD"
        rows.append({"Aresta": f"({a}, {b})", "Multiplicidade": count, "Status": status})
    if max_rows is not None:
        return rows[:max_rows]
    return rows


def convexity_diagnostic_rows(model: SolidModel) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    vertices = np.asarray(model.vertices, dtype=float)
    for idx, face in enumerate(model.faces, start=1):
        pts = vertices[face.indices]
        d = float(np.dot(face.normal, pts[0]))
        signed = vertices @ face.normal - d
        mask = np.ones(len(vertices), dtype=bool)
        mask[list(face.indices)] = False
        outside = signed[mask]
        max_positive = float(np.max(outside)) if len(outside) else 0.0
        violations = int(np.sum(outside > CONVEXITY_TOL)) if len(outside) else 0
        rows.append({
            "Face": idx,
            "Lados": face.sides,
            "Violações": violations,
            "Máx. fora do semiespaço": max_positive,
            "Plano de suporte?": violations == 0,
        })
    return rows


def diagnose_model(model: SolidModel) -> TechnicalDiagnosticReport:
    messages: list[DiagnosticMessage] = []

    orientation_values = [face_orientation_dot(model, face) for face in model.faces]
    outward_ok = bool(orientation_values and min(orientation_values) > ORIENTATION_TOL)
    min_orientation = float(min(orientation_values)) if orientation_values else 0.0
    if outward_ok:
        messages.append(DiagnosticMessage("OK", "orientação", "Todas as normais apontam para fora em relação ao centro do sólido."))
    else:
        messages.append(DiagnosticMessage("CRÍTICO", "orientação", f"Há normal com orientação suspeita; menor produto escalar = {min_orientation:.3e}."))

    planarity_values = [face_planarity_error(model, face) for face in model.faces]
    max_planarity = float(max(planarity_values)) if planarity_values else 0.0
    planar_ok = max_planarity <= PLANARITY_TOL
    if planar_ok:
        messages.append(DiagnosticMessage("OK", "planaridade", f"Erro máximo relativo de planaridade ≈ {max_planarity:.2e}."))
    else:
        messages.append(DiagnosticMessage("AVISO", "planaridade", f"Há faces não perfeitamente planares; erro máximo relativo ≈ {max_planarity:.2e}."))

    edges = edge_multiplicities(model)
    boundary = sum(1 for c in edges.values() if c == 1)
    nonmanifold = sum(1 for c in edges.values() if c > 2)
    closed_manifold = bool(edges) and boundary == 0 and nonmanifold == 0
    if closed_manifold:
        messages.append(DiagnosticMessage("OK", "manifoldness", "Todas as arestas têm multiplicidade 2: malha fechada/manifold provável."))
    else:
        messages.append(DiagnosticMessage("AVISO", "manifoldness", f"Arestas de borda: {boundary}; arestas não-manifold: {nonmanifold}."))

    convex_rows = convexity_diagnostic_rows(model)
    convex_violations = int(sum(int(row["Violações"]) for row in convex_rows))
    max_convexity_violation = float(max((float(row["Máx. fora do semiespaço"]) for row in convex_rows), default=0.0))
    if convex_violations == 0:
        convexity = "convexo provável"
        messages.append(DiagnosticMessage("OK", "convexidade", "Todas as faces se comportam como planos de suporte."))
    else:
        convexity = "não convexo ou com faces internas/cruzadas"
        messages.append(DiagnosticMessage("AVISO", "convexidade", f"Foram detectadas {convex_violations} violações de semiespaço; use volume/dual com cautela."))

    if model.euler_characteristic == 2:
        messages.append(DiagnosticMessage("OK", "Euler", "V - E + F = 2."))
    else:
        messages.append(DiagnosticMessage("AVISO", "Euler", f"V - E + F = {model.euler_characteristic}."))

    if model.name in EXPERIMENTAL_SOLID_NAMES:
        status = "experimental"
        messages.append(DiagnosticMessage("AVISO", "confiabilidade", "Modelo experimental auditado: adequado para visualização, não para certificação métrica/topológica formal."))
    elif any(m.level == "CRÍTICO" for m in messages):
        status = "crítico"
    elif any(m.level == "AVISO" for m in messages):
        status = "aviso"
    else:
        status = "ok"

    return TechnicalDiagnosticReport(
        name=model.name,
        family=model.family,
        status=status,
        vertex_count=int(len(model.vertices)),
        edge_count=int(model.edge_count),
        face_count=int(len(model.faces)),
        euler=int(model.euler_characteristic),
        outward_normals_ok=outward_ok,
        min_orientation_dot=min_orientation,
        max_planarity_error=max_planarity,
        planar_faces_ok=planar_ok,
        closed_manifold=closed_manifold,
        boundary_edge_count=int(boundary),
        nonmanifold_edge_count=int(nonmanifold),
        convexity=convexity,
        convexity_violations=convex_violations,
        max_convexity_violation=max_convexity_violation,
        messages=tuple(messages),
    )


def technical_report_html(model: SolidModel) -> str:
    import html

    report = diagnose_model(model)

    def table(rows: Sequence[dict[str, Any]], max_rows: int | None = None) -> str:
        rows = list(rows if max_rows is None else rows[:max_rows])
        if not rows:
            return "<p>Nenhum dado.</p>"
        headers = list(rows[0].keys())
        thead = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)
        body = []
        for row in rows:
            body.append("<tr>" + "".join(f"<td>{html.escape(str(row.get(h, '')))}</td>" for h in headers) + "</tr>")
        return f"<table><thead><tr>{thead}</tr></thead><tbody>{''.join(body)}</tbody></table>"

    css = """
<style>
body{font-family:Arial,sans-serif;line-height:1.45;margin:32px;max-width:1200px}table{border-collapse:collapse;width:100%;margin:12px 0 24px}td,th{border:1px solid #ddd;padding:6px 8px;text-align:left}th{background:#f3f4f6}.ok{color:#166534}.warn{color:#92400e}.crit{color:#991b1b}code{background:#f3f4f6;padding:2px 5px;border-radius:4px}
</style>
"""
    summary = report.to_summary_row()
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>PolyExplode v0.6 — Diagnóstico técnico</title>{css}</head>
<body>
<h1>PolyExplode Streamlit v0.6 — Diagnóstico técnico</h1>
<h2>{html.escape(model.name)}</h2>
<p><strong>Status:</strong> <code>{html.escape(report.status)}</code> · <strong>Família:</strong> {html.escape(model.family)}</p>
<h2>Resumo</h2>
{table([summary])}
<h2>Mensagens</h2>
{table(report.message_rows())}
<h2>Faces: orientação, normais externas e planaridade</h2>
{table(face_diagnostic_rows(model))}
<h2>Arestas: manifoldness</h2>
{table(edge_diagnostic_rows(model))}
<h2>Convexidade por semiespaços</h2>
{table(convexity_diagnostic_rows(model))}
<p>Notas: a convexidade é diagnosticada por teste de semiespaço das faces; a planaridade é relativa ao raio normalizado do modelo. O relatório técnico não transforma modelos experimentais em canônicos.</p>
</body></html>"""


def catalog_diagnostic_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in SOLID_NAMES:
        model = build_solid_from_definition(get_solid_definition(name))
        rows.append(diagnose_model(model).to_summary_row())
    return rows


def internal_catalog_validation_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in SOLID_NAMES:
        model = build_solid_from_definition(get_solid_definition(name))
        report = validate_built_model(model)
        tech = diagnose_model(model)
        is_experimental = name in EXPERIMENTAL_SOLID_NAMES
        warning_count = sum(1 for msg in report.messages if msg.level == "AVISO") + sum(1 for msg in tech.messages if msg.level == "AVISO")
        critical_count = sum(1 for msg in report.messages if msg.level == "CRÍTICO") + sum(1 for msg in tech.messages if msg.level == "CRÍTICO")
        if critical_count:
            status = "crítico"
            message = "Falha crítica na validação interna."
        elif is_experimental:
            status = "experimental"
            message = "Modelo mantido para visualização, com aviso explícito de malha problemática."
        elif not tech.closed_manifold:
            status = "atenção"
            message = "Malha não-manifold detectada em modelo não experimental."
        elif warning_count:
            status = "didático-com-aviso"
            message = "Malha fechada, mas há aproximações didáticas/planaridade/convexidade imperfeita."
        else:
            status = "ok"
            message = "Malha interna fechada/manifold provável, normais externas e planaridade dentro da tolerância."
        rows.append(InternalCatalogValidation(
            name=name,
            status=status,
            closed_manifold=bool(tech.closed_manifold),
            euler=int(tech.euler),
            max_planarity_error=float(tech.max_planarity_error),
            warning_count=int(warning_count),
            critical_count=int(critical_count),
            message=message,
        ).to_row())
    return rows
