from __future__ import annotations

from html import escape
import json
import re
import unicodedata

from . import __version__
from .anatomy import automatic_explanation, build_html_report, piece_rows, reliability_tag, teacher_questions
from .core import SolidModel, build_dual_graph, face_filter_options
from .decomposition import decomposition_info, decomposition_rows
from .custom_import import MeshValidationReport
from .diagnostics import diagnose_model, edge_diagnostic_rows, face_diagnostic_rows, convexity_diagnostic_rows
from .duality import dual_comparison_rows, duality_explanation, expected_dual_name, guided_duality_rows
from .lessons import build_lesson_html, build_lesson_text, lesson_json, lesson_questions, guided_sequence, level_profile
from .render_plotly import RenderOptions


def safe_file_slug(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()
    return normalized or "polyexplode"


def home_card(title: str, text: str) -> str:
    return (
        "<div class='home-card'>"
        f"<h3>{escape(title)}</h3>"
        f"<p>{escape(text)}</p>"
        "</div>"
    )


def badge_html(text: str) -> str:
    return f"<span class='badge'>{escape(text)}</span>"


def dual_step_html(etapa: int, titulo: str, descricao: str) -> str:
    return (
        "<div class='dual-step'>"
        f"<strong>Etapa {int(etapa)}: {escape(titulo)}</strong><br>"
        f"{escape(descricao)}"
        "</div>"
    )


def lesson_step_html(step: dict[str, str]) -> str:
    return (
        "<div class='lesson-step'>"
        f"<strong>{escape(str(step.get('Etapa', 'Etapa')))}</strong><br>"
        f"<strong>Ação:</strong> {escape(str(step.get('Ação do professor/estudante', '')))}<br>"
        f"<strong>Registro:</strong> {escape(str(step.get('O que registrar', '')))}"
        "</div>"
    )


def default_render_options(
    *,
    explosion: float = 0.0,
    face_filter: str = "Todas",
    color_mode: str = "Por tipo de face",
    decomposition_mode: str = "Pirâmides face-centro",
    show_ghost: bool = True,
    show_dual: bool = False,
    dual_progress: float = 1.0,
    dual_follow_explosion: bool = True,
    show_edges: bool = True,
    show_center: bool = True,
    show_normals: bool = False,
    show_labels: bool = False,
    silent_mode: bool = False,
    height: int = 720,
) -> RenderOptions:
    return RenderOptions(
        explosion=explosion,
        face_filter=face_filter,
        color_mode=color_mode,
        decomposition_mode=decomposition_mode,
        show_ghost=show_ghost,
        show_dual=show_dual,
        dual_progress=dual_progress,
        dual_follow_explosion=dual_follow_explosion,
        show_edges=show_edges,
        show_center=show_center,
        show_normals=show_normals,
        show_labels=show_labels,
        silent_mode=silent_mode,
        adaptive_legend=True,
        legend_threshold=14,
        height=height,
    )


def manifest_json(model: SolidModel, import_report: MeshValidationReport | None = None, lesson_level: str = "Médio") -> str:
    dual = build_dual_graph(model)
    reliability, reliability_note = reliability_tag(model)
    data = {
        "project": "PolyExplode Streamlit",
        "version": __version__,
        "edition": "v0.7.2 Cloud Hardening",
        "solid": model.summary(),
        "automatic_explanation": automatic_explanation(model),
        "reliability": {"tag": reliability, "note": reliability_note},
        "piece_table": piece_rows(model),
        "teacher_questions": teacher_questions(model),
        "guided_lesson": json.loads(lesson_json(model, lesson_level)),
        "dual_explorer": {
            "expected_dual": expected_dual_name(model),
            "explanation": duality_explanation(model),
            "comparison": dual_comparison_rows(model),
            "guided_steps": guided_duality_rows(model),
        },
        "dual_graph": dual.to_jsonable(),
        "mathematical_diagnostics": diagnose_model(model).to_jsonable(),
        "decomposition_modes": {
            "current": decomposition_info(model, "Pirâmides face-centro").to_jsonable(),
            "available": [decomposition_info(model, mode).to_jsonable() for mode in ["Pirâmides face-centro", "Faces", "Componentes", "Camadas", "Vértices/arestas/faces"]],
        },
        "import_validation": import_report.to_jsonable() if import_report else None,
        "face_type_filters": face_filter_options(model),
        "faces": [face.to_jsonable() for face in model.faces],
        "audit_hardening": {
            "adaptive_legend": True,
            "silent_mode_available": True,
            "internal_catalog_validation": "catalog page and automated tests",
            "experimental_models": "J6/J10 rotunda variants are explicitly marked as experimental when present.",
        },
        "dual_overlay_alignment": {
            "follow_explosion_available": True,
            "default_mode": "acompanha explosão",
            "fixed_dual_warning_threshold": 0.30,
        },
        "mathematical_diagnostics_v0_6": {
            "face_orientation": "normal externa por produto escalar com centro da face",
            "planarity": "erro relativo de distância ao plano da face",
            "manifoldness": "multiplicidade de arestas",
            "convexity": "teste de semiespaços por face",
            "technical_html_report": True,
        },
        "decomposition_modes_v0_7": {
            "faces": "placas poligonais afastadas",
            "pyramids": "pirâmides face-centro volumétricas",
            "components": "componentes conectados por adjacência de arestas",
            "layers": "camadas inferior/equatorial/superior",
            "topology": "vértices/arestas/faces separados"
        },
        "notes": [
            "Protótipo web em Streamlit + Plotly.",
            "Decomposição visual por pirâmides face-centro.",
            "Sem exportação STL nesta linha do projeto.",
            "v0.5.1 acrescenta validação interna do catálogo, legenda adaptativa, modo silencioso, sidebar contextual e escape de HTML.",
            "v0.5.2 acrescenta alinhamento opcional do dual visual com a explosão das faces e aviso para dual fixo em explosão alta.",
            "v0.6 acrescenta diagnóstico matemático: orientação de faces, normais externas, planaridade, manifoldness, convexidade e relatório técnico.",
            "v0.7 acrescenta modos de decomposição: faces, pirâmides, componentes, camadas e V/E/F.",
            "v0.7.2 remove chamadas depreciadas do Streamlit, reforça CI e consolida deploy em nuvem.",
            "O dual visual usa centros de faces e adjacência combinatória; não substitui certificação métrica canônica.",
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def _html_table(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "<p>Nenhum dado.</p>"
    headers = list(rows[0].keys())
    thead = "".join(f"<th>{escape(str(h))}</th>" for h in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{escape(str(row.get(h, '')))}</td>" for h in headers) + "</tr>")
    return f"<table><thead><tr>{thead}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def merged_html_report(model: SolidModel, import_report: MeshValidationReport | None = None, lesson_level: str = "Médio") -> str:
    """Extend the didactic report with duality, validation and lesson blocks.

    All inserted text is escaped here; exported HTML is safe for catalog names and
    user-provided imported solid names.
    """
    base = build_html_report(model)
    import_block = ""
    if import_report is not None:
        import_block = f"""
<h2>Validação de importação — v0.6</h2>
<p><strong>Formato:</strong> {escape(import_report.format)} · <strong>Convexidade:</strong> {escape(import_report.convexity)} · <strong>Malha fechada provável:</strong> {escape(str(import_report.closed_manifold))}</p>
{_html_table(import_report.rows())}
"""
    profile = level_profile(lesson_level)
    lesson_block = f"""
<h2>Aula guiada — v0.7.2</h2>
<p><strong>Nível:</strong> {escape(profile.level)} · <strong>Público:</strong> {escape(profile.audience)}</p>
<p><strong>Foco:</strong> {escape(profile.focus)}</p>
{_html_table(guided_sequence(model, profile.level))}
<h3>Perguntas da atividade</h3>
{_html_table(lesson_questions(model, profile.level))}
"""
    dual_block = f"""
<h2>Explorador de dualidade — v0.7.2</h2>
<p>{escape(duality_explanation(model))}</p>
<p><strong>Dual esperado:</strong> {escape(expected_dual_name(model))}</p>
{_html_table(guided_duality_rows(model))}
"""
    decomposition_block = f"""
<h2>Modos de decomposição — v0.7.2</h2>
<p>A v0.7.2 mantém os modos da v0.7 e acrescenta prontidão para GitHub/Streamlit Cloud.</p>
{_html_table(decomposition_rows(model, "Vértices/arestas/faces"))}
"""
    diagnostic = diagnose_model(model)
    diagnostics_block = f"""
<h2>Diagnóstico matemático — v0.7.2</h2>
<p><strong>Status:</strong> {escape(diagnostic.status)} · <strong>Normais externas:</strong> {escape(str(diagnostic.outward_normals_ok))} · <strong>Manifold fechado:</strong> {escape(str(diagnostic.closed_manifold))} · <strong>Convexidade:</strong> {escape(diagnostic.convexity)}</p>
<h3>Mensagens</h3>
{_html_table(diagnostic.message_rows())}
<h3>Faces: orientação e planaridade</h3>
{_html_table(face_diagnostic_rows(model))}
<h3>Arestas: manifoldness</h3>
{_html_table(edge_diagnostic_rows(model))}
<h3>Convexidade</h3>
{_html_table(convexity_diagnostic_rows(model))}
"""
    audit_block = """
<h2>Higiene de auditoria, dual, decomposição e cloud — v0.7.2</h2>
<p>A v0.5.1 adicionou legenda adaptativa, modo silencioso, validação interna do catálogo e escape de HTML nos blocos gerados pelo aplicativo.</p>
<p>A v0.5.2 adicionou alinhamento do dual visual com a explosão: quando ativado, cada vértice dual acompanha a face/pirâmide correspondente.</p>
<p>A v0.6 adiciona diagnóstico matemático técnico: orientação de faces, normais externas, planaridade, manifoldness e convexidade.</p>
<p>A v0.7 adiciona modos de decomposição: faces, pirâmides, componentes, camadas e V/E/F.</p>
<p>A v0.7.2 adiciona arquivos de repositório, CI, licença, changelog, exemplos de importação e roteiro de Streamlit Cloud.</p>
"""
    return base.replace("</body>", import_block + lesson_block + dual_block + decomposition_block + diagnostics_block + audit_block + "</body>")
