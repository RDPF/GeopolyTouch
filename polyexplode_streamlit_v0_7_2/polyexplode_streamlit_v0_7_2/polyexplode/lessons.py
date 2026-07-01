from __future__ import annotations

from dataclasses import dataclass
from html import escape
import json
from typing import Iterable

from .anatomy import face_histogram_text, piece_rows, teacher_questions
from .core import SolidModel, face_type_name
from .duality import expected_dual_name


LESSON_LEVELS = ["Fundamental", "Médio", "Licenciatura", "Engenharia"]


@dataclass(frozen=True)
class LessonProfile:
    level: str
    audience: str
    focus: str
    objectives: tuple[str, ...]
    vocabulary: tuple[str, ...]


def level_profile(level: str) -> LessonProfile:
    if level not in LESSON_LEVELS:
        level = "Médio"
    profiles = {
        "Fundamental": LessonProfile(
            level="Fundamental",
            audience="Ensino Fundamental — anos finais",
            focus="observar, contar, comparar e reconhecer peças geométricas",
            objectives=(
                "Reconhecer faces, arestas e vértices em um poliedro.",
                "Relacionar cada face a uma peça da explosão.",
                "Identificar os tipos de polígonos presentes nas faces.",
            ),
            vocabulary=("face", "aresta", "vértice", "pirâmide", "montar/desmontar"),
        ),
        "Médio": LessonProfile(
            level="Médio",
            audience="Ensino Médio",
            focus="Euler, volume por decomposição e dualidade visual",
            objectives=(
                "Verificar a característica de Euler V − E + F.",
                "Interpretar a decomposição em pirâmides face-centro como soma de volumes.",
                "Compreender que centros de faces geram um dual visual.",
            ),
            vocabulary=("Euler", "volume", "base", "altura", "dual", "decomposição"),
        ),
        "Licenciatura": LessonProfile(
            level="Licenciatura",
            audience="Licenciatura em Matemática ou formação docente",
            focus="mediação didática, visualização, argumentação e limitações do modelo",
            objectives=(
                "Planejar uma mediação didática baseada em observação, decomposição e reconstrução.",
                "Discutir a passagem entre representação visual, topologia e métrica.",
                "Avaliar limites da decomposição para sólidos importados, não convexos ou didáticos.",
            ),
            vocabulary=("mediação", "topologia", "métrica", "dualidade", "representação", "validação"),
        ),
        "Engenharia": LessonProfile(
            level="Engenharia",
            audience="Engenharia, computação gráfica ou geometria computacional aplicada",
            focus="malha, validação, normais, convexidade e cálculo geométrico",
            objectives=(
                "Interpretar uma malha poliedral por vértices, faces, arestas e normais.",
                "Relacionar área, altura e volume em cada pirâmide face-centro.",
                "Avaliar riscos de interpretação quando a malha é aberta, não convexa ou não-manifold.",
            ),
            vocabulary=("malha", "normal", "convexidade", "manifold", "área vetorial", "grafo dual"),
        ),
    }
    return profiles[level]


def _objective_text(profile: LessonProfile) -> str:
    return " ".join(profile.objectives)


def guided_sequence(model: SolidModel, level: str = "Médio") -> list[dict[str, str]]:
    profile = level_profile(level)
    summary = model.summary()
    face_text = face_histogram_text(model)
    dual = expected_dual_name(model)
    steps = [
        {
            "Etapa": "1. Observar o sólido",
            "Ação do professor/estudante": f"Gire o {model.name} no visualizador e observe a família {model.family}.",
            "O que registrar": f"O sólido tem {summary['vertices']} vértices, {summary['edges']} arestas e {summary['faces']} faces.",
        },
        {
            "Etapa": "2. Contar V, E e F",
            "Ação do professor/estudante": "Use o painel de métricas e confira a relação de Euler.",
            "O que registrar": f"V − E + F = {summary['vertices']} − {summary['edges']} + {summary['faces']} = {summary['euler']}.",
        },
        {
            "Etapa": "3. Explodir por faces",
            "Ação do professor/estudante": "Aumente o afastamento e acompanhe cada face virando a base de uma pirâmide.",
            "O que registrar": f"Como há {summary['faces']} faces, aparecem {summary['faces']} peças na explosão.",
        },
        {
            "Etapa": "4. Identificar as peças",
            "Ação do professor/estudante": "Observe as cores por tipo de face e compare com a tabela das peças.",
            "O que registrar": f"As bases das peças correspondem às faces originais: {face_text}.",
        },
        {
            "Etapa": "5. Comparar com o dual",
            "Ação do professor/estudante": "Ative o Dual Explorer e mova o progresso do dual de 0 a 1.",
            "O que registrar": f"O app sugere como dual visual: {dual}. Faces do original viram vértices do dual.",
        },
        {
            "Etapa": "6. Responder e discutir",
            "Ação do professor/estudante": "Use as perguntas com gabarito e peça uma justificativa escrita ou oral.",
            "O que registrar": f"Foco da atividade para {profile.level}: {profile.focus}.",
        },
    ]
    if profile.level == "Engenharia":
        steps.insert(5, {
            "Etapa": "5A. Validar a interpretação geométrica",
            "Ação do professor/estudante": "Verifique etiqueta de confiabilidade, convexidade e possíveis avisos de importação.",
            "O que registrar": "A soma volumétrica é mais segura para sólidos fechados, convexos e com faces bem orientadas.",
        })
    if profile.level == "Licenciatura":
        steps.append({
            "Etapa": "7. Planejar mediação",
            "Ação do professor/estudante": "Reescreva uma das perguntas para uma turma real e descreva a intervenção docente.",
            "O que registrar": "Indique que representação visual ajuda e que limite matemático precisa ser explicitado.",
        })
    return steps


def lesson_questions(model: SolidModel, level: str = "Médio") -> list[dict[str, str]]:
    profile = level_profile(level)
    summary = model.summary()
    pieces = piece_rows(model)
    max_piece = max(pieces, key=lambda row: float(row["Volume da peça"])) if pieces else None
    base = teacher_questions(model)
    rows: list[dict[str, str]] = []

    def add(q: str, a: str, objective: str) -> None:
        rows.append({"Nível": profile.level, "Pergunta": q, "Resposta esperada": a, "Objetivo": objective})

    if profile.level == "Fundamental":
        add(
            f"Ao desmontar o {model.name}, quantas peças aparecem?",
            f"Aparecem {summary['faces']} peças, uma para cada face.",
            "Contar faces e relacionar face↔peça.",
        )
        add(
            "Que tipos de polígonos formam as bases das peças?",
            f"As bases são: {face_histogram_text(model)}.",
            "Reconhecer polígonos nas faces.",
        )
        add(
            "O sólido fica diferente quando explodimos apenas um tipo de face?",
            "Sim. Apenas as faces selecionadas se afastam; as demais permanecem próximas do sólido original.",
            "Comparar partes e todo.",
        )
    elif profile.level == "Médio":
        for item in base[:5]:
            add(item["Pergunta"], item["Resposta esperada"], "Relacionar estrutura, volume e Euler.")
        add(
            "Por que o dual visual nasce dos centros das faces?",
            "Porque cada face do sólido original é representada por um ponto no dual, e faces vizinhas geram arestas no dual.",
            "Compreender dualidade visual.",
        )
    elif profile.level == "Licenciatura":
        add(
            "Como você explicaria a decomposição para estudantes que ainda confundem face e peça?",
            "Mostraria primeiro o sólido inteiro, depois uma face destacada e só então a pirâmide cuja base é aquela face.",
            "Planejar mediação didática.",
        )
        add(
            "Que cuidado conceitual precisa ser dito sobre modelos didáticos/topológicos?",
            "Eles podem ser úteis para conectividade e visualização, mas não garantem certificação métrica canônica.",
            "Distinguir topologia, métrica e representação.",
        )
        for item in base[:4]:
            add(item["Pergunta"], item["Resposta esperada"], "Transformar observação em argumentação matemática.")
    else:  # Engenharia
        add(
            "Que hipótese torna a soma dos volumes por pirâmides mais confiável?",
            "Malha fechada, faces orientáveis, boa planicidade e sólido convexo ou adequadamente estrelado em relação ao centro usado.",
            "Avaliar validade geométrica do cálculo.",
        )
        add(
            "O que uma normal externa representa na explosão?",
            "Ela define a direção de afastamento da peça e indica a orientação local da face.",
            "Relacionar normal, orientação e visualização 3D.",
        )
        if max_piece:
            add(
                "Qual peça tem maior volume na tabela atual?",
                f"Na tabela arredondada, a peça {max_piece['Peça']} tem volume {max_piece['Volume da peça']}.",
                "Ler e interpretar dados geométricos da malha.",
            )
        add(
            "Por que um OFF aberto ou não-manifold exige aviso?",
            "Porque a conectividade pode impedir interpretação volumétrica e dualidade combinatória confiáveis.",
            "Validar malhas antes de interpretar resultados.",
        )
    return rows


def lesson_summary(model: SolidModel, level: str = "Médio") -> dict[str, object]:
    profile = level_profile(level)
    return {
        "level": profile.level,
        "audience": profile.audience,
        "focus": profile.focus,
        "objectives": list(profile.objectives),
        "vocabulary": list(profile.vocabulary),
        "steps": guided_sequence(model, profile.level),
        "questions": lesson_questions(model, profile.level),
        "solid": model.summary(),
    }


def _table(headers: Iterable[str], rows: Iterable[dict[str, object]]) -> str:
    headers = list(headers)
    head = "".join(f"<th>{escape(str(h))}</th>" for h in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{escape(str(row.get(h, '')))}</td>" for h in headers) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def build_lesson_text(model: SolidModel, level: str = "Médio") -> str:
    profile = level_profile(level)
    summary = model.summary()
    lines = [
        f"POLYEXPLODE — ATIVIDADE GUIADA ({profile.level})",
        f"Sólido: {model.name}",
        f"Público: {profile.audience}",
        f"Foco: {profile.focus}",
        "",
        "Objetivos:",
    ]
    lines += [f"- {obj}" for obj in profile.objectives]
    lines += [
        "",
        "Dados do sólido:",
        f"- Vértices: {summary['vertices']}",
        f"- Arestas: {summary['edges']}",
        f"- Faces/peças: {summary['faces']}",
        f"- Euler: {summary['euler']}",
        f"- Faces: {face_histogram_text(model)}",
        f"- Dual visual sugerido: {expected_dual_name(model)}",
        "",
        "Sequência didática guiada:",
    ]
    for row in guided_sequence(model, profile.level):
        lines += [
            f"{row['Etapa']}",
            f"  Ação: {row['Ação do professor/estudante']}",
            f"  Registro: {row['O que registrar']}",
        ]
    lines += ["", "Perguntas com gabarito:"]
    for i, row in enumerate(lesson_questions(model, profile.level), start=1):
        lines += [
            f"{i}. {row['Pergunta']}",
            f"   Resposta esperada: {row['Resposta esperada']}",
            f"   Objetivo: {row['Objetivo']}",
        ]
    lines += [
        "",
        "Observação: esta atividade usa decomposição visual por pirâmides face-centro. Para malhas importadas, não convexas ou problemáticas, interprete volume e dualidade com cautela.",
    ]
    return "\n".join(lines)


def build_lesson_html(model: SolidModel, level: str = "Médio") -> str:
    profile = level_profile(level)
    summary = model.summary()
    steps = guided_sequence(model, profile.level)
    questions = lesson_questions(model, profile.level)
    objectives = "".join(f"<li>{escape(obj)}</li>" for obj in profile.objectives)
    vocab = ", ".join(escape(v) for v in profile.vocabulary)
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>PolyExplode — Atividade guiada — {escape(model.name)}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 32px; line-height: 1.5; color: #202124; }}
h1, h2 {{ color: #111827; }}
.badge {{ display:inline-block; padding: 6px 10px; border-radius: 999px; background:#eef2ff; color:#312e81; font-weight:700; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px 0; font-size: 14px; }}
th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; vertical-align: top; }}
th {{ background: #f3f4f6; }}
.kpis {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 18px 0; }}
.kpi {{ border: 1px solid #d1d5db; border-radius: 8px; padding: 12px; background:#fafafa; }}
.kpi strong {{ display:block; font-size:22px; }}
.note {{ background:#fff7ed; border-left: 4px solid #f97316; padding: 12px 14px; }}
</style>
</head>
<body>
<h1>PolyExplode — Atividade guiada</h1>
<p><span class="badge">{escape(profile.level)}</span></p>
<p><strong>Sólido:</strong> {escape(model.name)} · <strong>Público:</strong> {escape(profile.audience)}</p>
<p><strong>Foco:</strong> {escape(profile.focus)}</p>
<h2>Objetivos</h2>
<ul>{objectives}</ul>
<p><strong>Vocabulário-chave:</strong> {vocab}</p>
<div class="kpis">
<div class="kpi">Vértices<strong>{summary['vertices']}</strong></div>
<div class="kpi">Arestas<strong>{summary['edges']}</strong></div>
<div class="kpi">Faces/peças<strong>{summary['faces']}</strong></div>
<div class="kpi">Euler χ<strong>{summary['euler']}</strong></div>
<div class="kpi">Dual<strong>{escape(expected_dual_name(model))}</strong></div>
</div>
<div class="note"><strong>Faces:</strong> {escape(face_histogram_text(model))}. Cada face gera uma pirâmide com ápice no centro do sólido.</div>
<h2>Sequência didática guiada</h2>
{_table(["Etapa", "Ação do professor/estudante", "O que registrar"], steps)}
<h2>Perguntas com gabarito</h2>
{_table(["Pergunta", "Resposta esperada", "Objetivo"], questions)}
<p><em>Gerado pelo PolyExplode Streamlit v0.5 — Guided Lessons. Sem exportação STL.</em></p>
</body>
</html>"""


def lesson_json(model: SolidModel, level: str = "Médio") -> str:
    return json.dumps(lesson_summary(model, level), ensure_ascii=False, indent=2)
