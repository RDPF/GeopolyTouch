from __future__ import annotations

from collections import Counter
from html import escape
from typing import Iterable

from .core import SolidModel, build_dual_graph, face_type_name


DUAL_HINTS: dict[str, str] = {
    "Cubo": "Octaedro",
    "Octaedro": "Cubo",
    "Dodecaedro": "Icosaedro",
    "Icosaedro": "Dodecaedro",
    "Tetraedro": "Tetraedro",
    "Cuboctaedro": "Dodecaedro rômbico",
    "Icosidodecaedro": "Triacontaedro rômbico",
    "Icosaedro truncado": "Pentakis dodecaedro",
    "Tetraedro truncado": "Triakis tetraedro",
    "Cubo truncado": "Tetrakis hexaedro",
    "Octaedro truncado": "Triakis octaedro",
}


RELIABILITY_HELP: dict[str, str] = {
    "métrico-exato": "Modelo catalogado com coordenadas explícitas ou operação clássica suficientemente estável para visualização métrica didática.",
    "paramétrico-estável": "Família paramétrica construída por fórmula; adequada para explosão, métricas e comparação topológica.",
    "derivado-didático": "Modelo derivado por retificação, truncamento ou dualidade polar; excelente para ensino, mas não é certificado como malha canônica final.",
    "topológico-didático": "Modelo adequado para explicar faces, peças e conectividade; não deve ser usado como certificação métrica de Johnson regular.",
    "importado-validado": "Modelo carregado por OFF/JSON e validado pelo app. A etiqueta depende da malha fornecida pelo usuário, não de um catálogo canônico.",
    "experimental-auditado": "Modelo experimental preservado apenas para exploração visual: a auditoria interna detectou malha não-manifold ou problema geométrico conhecido.",
}


def reliability_tag(model: SolidModel) -> tuple[str, str]:
    """Return a compact reliability label and an explanatory note."""
    family = model.family.lower()
    note = (model.note or "").lower()
    if "experimental" in family or "experimental" in note or "não-manifold" in note:
        key = "experimental-auditado"
    elif "importado" in family:
        key = "importado-validado"
    elif "johnson" in family or "topologia" in note or ("didático" in note and "j" in model.name.lower()):
        key = "topológico-didático"
    elif any(word in family for word in ["arquimedianos", "catalan", "trapezoedros"]):
        key = "derivado-didático"
    elif any(word in family for word in ["prismas", "antiprismas", "pirâmides", "bipirâmides"]):
        key = "paramétrico-estável"
    else:
        key = "métrico-exato"
    return key, RELIABILITY_HELP[key]


def face_histogram_text(model: SolidModel) -> str:
    parts: list[str] = []
    for sides, count in model.face_histogram.items():
        label = face_type_name(sides).lower()
        parts.append(f"{count} {label}")
    if not parts:
        return "sem faces registradas"
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " e " + parts[-1]


def automatic_explanation(model: SolidModel) -> str:
    summary = model.summary()
    pieces = summary["faces"]
    face_text = face_histogram_text(model)
    dual_name = DUAL_HINTS.get(model.name)
    dual_sentence = (
        f"Ao ligar os centros das faces, aparece visualmente o dual associado: {dual_name}."
        if dual_name
        else "Ao ligar os centros das faces, surge um grafo dual visual que mostra a vizinhança entre as faces."
    )
    reliability, _ = reliability_tag(model)
    return (
        f"O sólido {model.name} pertence à família {model.family}. Ele possui "
        f"{summary['vertices']} vértices, {summary['edges']} arestas e {summary['faces']} faces, "
        f"com característica de Euler χ = {summary['euler']}. "
        f"Suas faces são compostas por {face_text}. "
        f"Nesta decomposição, cada face vira a base de uma pirâmide cujo ápice é o centro do sólido; "
        f"por isso a explosão produz {pieces} peças. "
        f"A soma dos volumes das peças recompõe o volume exibido pelo app, calculado por área da base × altura / 3. "
        f"{dual_sentence} Etiqueta de confiabilidade: {reliability}."
    )


def piece_rows(model: SolidModel) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, face in enumerate(model.faces, start=1):
        volume = face.area * face.distance_to_center / 3.0
        rows.append({
            "Peça": idx,
            "Tipo": face_type_name(face.sides),
            "Lados da base": face.sides,
            "Área da base": round(float(face.area), 6),
            "Altura até o centro": round(float(face.distance_to_center), 6),
            "Volume da peça": round(float(volume), 6),
            "Centro x": round(float(face.center[0]), 6),
            "Centro y": round(float(face.center[1]), 6),
            "Centro z": round(float(face.center[2]), 6),
            "Normal x": round(float(face.normal[0]), 6),
            "Normal y": round(float(face.normal[1]), 6),
            "Normal z": round(float(face.normal[2]), 6),
        })
    return rows


def teacher_questions(model: SolidModel) -> list[dict[str, str]]:
    summary = model.summary()
    face_text = face_histogram_text(model)
    dual = DUAL_HINTS.get(model.name, "o grafo dual visual formado pelos centros das faces")
    most_common_sides, most_common_count = Counter(face.sides for face in model.faces).most_common(1)[0]
    most_common_label = face_type_name(most_common_sides).lower()
    return [
        {
            "Pergunta": f"Quantas peças aparecem quando explodimos o {model.name} por pirâmides face-centro?",
            "Resposta esperada": f"Aparecem {summary['faces']} peças, porque há uma pirâmide para cada face do sólido.",
        },
        {
            "Pergunta": "Qual é a relação entre V, E, F e a característica de Euler neste modelo?",
            "Resposta esperada": f"V - E + F = {summary['vertices']} - {summary['edges']} + {summary['faces']} = {summary['euler']}.",
        },
        {
            "Pergunta": "Que tipos de bases aparecem nas pirâmides da explosão?",
            "Resposta esperada": f"As bases correspondem às faces originais: {face_text}.",
        },
        {
            "Pergunta": "Como o volume total é reconstruído a partir das peças?",
            "Resposta esperada": "Somando o volume de cada pirâmide, calculado por área da base × altura até o centro dividido por 3.",
        },
        {
            "Pergunta": "Qual tipo de face aparece com maior frequência neste sólido?",
            "Resposta esperada": f"O tipo mais frequente é {most_common_label}, com {most_common_count} ocorrência(s).",
        },
        {
            "Pergunta": "O que o dual visual representa?",
            "Resposta esperada": f"Ele representa os centros das faces e as adjacências entre faces; para este sólido, o app sugere: {dual}.",
        },
    ]


def _html_table(headers: Iterable[str], rows: Iterable[dict[str, object]]) -> str:
    headers = list(headers)
    head = "".join(f"<th>{escape(str(h))}</th>" for h in headers)
    body_rows: list[str] = []
    for row in rows:
        cells = "".join(f"<td>{escape(str(row.get(h, '')))}</td>" for h in headers)
        body_rows.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def build_html_report(model: SolidModel) -> str:
    summary = model.summary()
    reliability, reliability_note = reliability_tag(model)
    pieces = piece_rows(model)
    questions = teacher_questions(model)
    piece_headers = ["Peça", "Tipo", "Lados da base", "Área da base", "Altura até o centro", "Volume da peça"]
    question_headers = ["Pergunta", "Resposta esperada"]
    explanation = automatic_explanation(model)
    dual = build_dual_graph(model)
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatório PolyExplode — {escape(model.name)}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 32px; line-height: 1.48; color: #202124; }}
h1, h2 {{ color: #111827; }}
.badge {{ display:inline-block; padding: 6px 10px; border-radius: 999px; background:#eef2ff; color:#312e81; font-weight:700; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px 0; font-size: 14px; }}
th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; }}
th {{ background: #f3f4f6; }}
.kpis {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 18px 0; }}
.kpi {{ border: 1px solid #d1d5db; border-radius: 8px; padding: 12px; background:#fafafa; }}
.kpi strong {{ display:block; font-size:22px; }}
.note {{ background:#fff7ed; border-left: 4px solid #f97316; padding: 12px 14px; }}
</style>
</head>
<body>
<h1>Relatório PolyExplode — {escape(model.name)}</h1>
<p><span class="badge">{escape(reliability)}</span></p>
<p>{escape(explanation)}</p>
<div class="note"><strong>Confiabilidade:</strong> {escape(reliability_note)}</div>
<div class="kpis">
<div class="kpi">Vértices<strong>{summary['vertices']}</strong></div>
<div class="kpi">Arestas<strong>{summary['edges']}</strong></div>
<div class="kpi">Faces/peças<strong>{summary['faces']}</strong></div>
<div class="kpi">Euler χ<strong>{summary['euler']}</strong></div>
<div class="kpi">Volume<strong>{summary['volume_by_face_pyramids']:.6f}</strong></div>
</div>
<h2>Anatomia das peças</h2>
{_html_table(piece_headers, pieces)}
<h2>Modo professor</h2>
{_html_table(question_headers, questions)}
<h2>Dual visual</h2>
<p>O dual visual possui {len(dual.vertices)} vértices e {len(dual.edges)} arestas. Ele é construído a partir dos centros das faces e da adjacência entre faces do sólido original.</p>
<p><em>Gerado pelo PolyExplode Streamlit v0.4 — Custom Import. Sem exportação STL.</em></p>
</body>
</html>"""
