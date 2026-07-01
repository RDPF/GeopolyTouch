from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .anatomy import DUAL_HINTS, face_histogram_text
from .core import SolidModel, build_dual_graph


@dataclass(frozen=True)
class DualityStep:
    etapa: int
    titulo: str
    descricao: str
    progresso: float


def expected_dual_name(model: SolidModel) -> str:
    """Return a human-readable expected dual name when known."""
    return DUAL_HINTS.get(model.name, "Dual visual combinatório")


def duality_explanation(model: SolidModel) -> str:
    summary = model.summary()
    dual = build_dual_graph(model)
    expected = expected_dual_name(model)
    return (
        f"No {model.name}, cada face do sólido original gera um vértice no dual. "
        f"Por isso o dual visual possui {len(dual.vertices)} vértices, que correspondem às {summary['faces']} faces originais. "
        f"Cada aresta do dual liga centros de faces vizinhas; no modelo atual aparecem {len(dual.edges)} arestas duais. "
        f"A leitura didática esperada para este caso é: {expected}."
    )


def dual_comparison_rows(model: SolidModel) -> list[dict[str, object]]:
    """Comparison table between the original solid and the visual dual."""
    summary = model.summary()
    dual = build_dual_graph(model)
    expected = expected_dual_name(model)
    return [
        {
            "Aspecto": "Nome",
            "Sólido original": model.name,
            "Dual visual": expected,
            "Interpretação": "O dual é obtido pelos centros das faces.",
        },
        {
            "Aspecto": "Vértices",
            "Sólido original": summary["vertices"],
            "Dual visual": len(dual.vertices),
            "Interpretação": "Vértices do dual = faces do original.",
        },
        {
            "Aspecto": "Arestas",
            "Sólido original": summary["edges"],
            "Dual visual": len(dual.edges),
            "Interpretação": "Arestas do dual representam adjacência entre faces.",
        },
        {
            "Aspecto": "Faces",
            "Sólido original": summary["faces"],
            "Dual visual": summary["vertices"],
            "Interpretação": "Faces do dual correspondem aos vértices do original, em leitura convexa ideal.",
        },
        {
            "Aspecto": "Tipos de face",
            "Sólido original": face_histogram_text(model),
            "Dual visual": "depende das valências dos vértices originais",
            "Interpretação": "A geometria do dual visual é combinatória, não certificação métrica final.",
        },
    ]


def guided_duality_steps(model: SolidModel) -> list[DualityStep]:
    expected = expected_dual_name(model)
    summary = model.summary()
    return [
        DualityStep(
            1,
            "Sólido original",
            f"Começamos com o {model.name}: V={summary['vertices']}, E={summary['edges']}, F={summary['faces']}.",
            0.0,
        ),
        DualityStep(
            2,
            "Centros das faces",
            "Cada face recebe um ponto em seu centro. Esses pontos serão os vértices do dual.",
            0.25,
        ),
        DualityStep(
            3,
            "Adjacência entre faces",
            "Quando duas faces compartilham uma aresta, ligamos os seus centros por uma aresta dual.",
            0.50,
        ),
        DualityStep(
            4,
            "Dual emergindo",
            "O grafo dual é afastado visualmente para que sua estrutura apareça sem se confundir com o sólido original.",
            0.78,
        ),
        DualityStep(
            5,
            "Comparação final",
            f"No fim, comparamos o sólido original com seu dual visual. Leitura sugerida: {expected}.",
            1.0,
        ),
    ]


def guided_duality_rows(model: SolidModel) -> list[dict[str, object]]:
    return [
        {
            "Etapa": step.etapa,
            "Título": step.titulo,
            "Progresso do dual": step.progresso,
            "O que observar": step.descricao,
        }
        for step in guided_duality_steps(model)
    ]
