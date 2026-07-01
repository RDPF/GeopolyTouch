from __future__ import annotations

from collections import Counter

import streamlit as st

from polyexplode import __version__
from polyexplode.anatomy import (
    automatic_explanation,
    face_histogram_text,
    piece_rows,
    reliability_tag,
    teacher_questions,
)
from polyexplode.core import build_dual_graph, build_solid_from_definition, face_filter_options
from polyexplode.custom_import import (
    MeshValidationReport,
    example_json_tetrahedron,
    example_off_cube,
    import_uploaded_solid,
    validation_rows,
)
from polyexplode.decomposition import (
    DECOMPOSITION_MODES,
    MODE_HELP,
    decomposition_info,
    decomposition_rows,
)
from polyexplode.diagnostics import (
    catalog_diagnostic_rows,
    convexity_diagnostic_rows,
    diagnose_model,
    edge_diagnostic_rows,
    face_diagnostic_rows,
    internal_catalog_validation_rows,
    technical_report_html,
)
from polyexplode.duality import (
    dual_comparison_rows,
    duality_explanation,
    expected_dual_name,
    guided_duality_rows,
    guided_duality_steps,
)
from polyexplode.lessons import (
    LESSON_LEVELS,
    build_lesson_html,
    build_lesson_text,
    guided_sequence,
    lesson_json,
    lesson_questions,
    level_profile,
)
from polyexplode.render_plotly import (
    build_dual_only_figure,
    build_duality_animation_figure,
    build_figure,
)
from polyexplode.solids import EXPERIMENTAL_SOLID_NAMES, SOLID_NAMES, catalog_metadata, get_solid_definition
from polyexplode.ui import (
    badge_html,
    default_render_options,
    dual_step_html,
    home_card,
    lesson_step_html,
    manifest_json,
    merged_html_report,
    safe_file_slug,
)


st.set_page_config(
    page_title="PolyExplode Streamlit",
    page_icon="💥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.home-card {
    border: 1px solid rgba(148, 163, 184, 0.35);
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 12px;
    background: rgba(15, 23, 42, 0.05);
}
.home-card h3 { margin-top: 0; margin-bottom: 6px; }
.small-muted { color: #64748b; font-size: 0.92rem; }
.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(99, 102, 241, 0.14);
    color: #c7d2fe;
    font-weight: 700;
    font-size: 0.82rem;
}
.dual-step {
    border-left: 4px solid #818cf8;
    padding: 10px 14px;
    margin: 8px 0 14px 0;
    background: rgba(99, 102, 241, 0.08);
    border-radius: 8px;
}
.lesson-step {
    border-left: 4px solid #f59e0b;
    padding: 10px 14px;
    margin: 8px 0 14px 0;
    background: rgba(245, 158, 11, 0.09);
    border-radius: 8px;
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def cached_catalog_metadata() -> dict[str, dict[str, str]]:
    return catalog_metadata()


@st.cache_resource(show_spinner=False)
def load_model(name: str):
    return build_solid_from_definition(get_solid_definition(name))


@st.cache_data(show_spinner=False)
def cached_catalog_validation_rows() -> list[dict[str, object]]:
    return internal_catalog_validation_rows()


@st.cache_data(show_spinner=False)
def cached_catalog_diagnostic_rows() -> list[dict[str, object]]:
    return catalog_diagnostic_rows()


def family_filtered_names(selected_family: str) -> list[str]:
    meta = cached_catalog_metadata()
    if selected_family == "Todas":
        return SOLID_NAMES
    return [name for name in SOLID_NAMES if meta[name]["family"] == selected_family]


def face_rows(model) -> list[dict[str, object]]:
    return [{"Tipo de face": f"{sides}-gonos", "Quantidade": count} for sides, count in model.face_histogram.items()]


def html_download(fig) -> str:
    return fig.to_html(include_plotlyjs="cdn", full_html=True)


def render_metrics(model, dual) -> None:
    summary = model.summary()
    cols = st.columns(6)
    cols[0].metric("V", summary["vertices"])
    cols[1].metric("E", summary["edges"])
    cols[2].metric("F / peças", summary["faces"])
    cols[3].metric("χ", summary["euler"])
    cols[4].metric("Volume", f'{summary["volume_by_face_pyramids"]:.4f}')
    cols[5].metric("Vértices do dual", len(dual.vertices))


def render_home(model, lesson_level: str) -> None:
    summary = model.summary()
    reliability, reliability_note = reliability_tag(model)
    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        st.subheader("v0.7.2 — Cloud Hardening")
        st.markdown(
            "Esta versão consolida a prontidão para Streamlit Cloud e mantém o diagnóstico matemático técnico: orientação das faces, normais externas, "
            "planaridade, manifoldness, convexidade e relatório HTML de qualidade geométrica."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sólidos", len(SOLID_NAMES))
        c2.metric("Experimentais", len(EXPERIMENTAL_SOLID_NAMES))
        c3.metric("Modos", "v0.7.2")
        c4.metric("Cloud", "hardened")
        st.markdown(home_card("1. Escolha um sólido", "Use a barra lateral para filtrar família e sólido. Cubo, octaedro, dodecaedro e icosaedro são bons pontos de partida."), unsafe_allow_html=True)
        st.markdown(home_card("2. Controle a explosão", "No Laboratório 3D, ajuste o afastamento e escolha se quer explodir todas as faces ou apenas um tipo."), unsafe_allow_html=True)
        st.markdown(home_card("3. Use modo silencioso", "Para capturas limpas, o modo silencioso remove legenda, normais e rótulos de face sem alterar a malha."), unsafe_allow_html=True)
        st.markdown(home_card("4. Alterne o modo", "Compare pirâmides, placas de face, componentes, camadas e a separação V/E/F."), unsafe_allow_html=True)
        st.markdown(home_card("5. Audite a geometria", "Use Diagnóstico matemático para verificar normais externas, planaridade, manifoldness, convexidade e Euler."), unsafe_allow_html=True)
    with right:
        st.subheader("Sólido atual")
        st.markdown(f"### {model.name}")
        st.markdown(badge_html(reliability), unsafe_allow_html=True)
        st.info(reliability_note)
        st.markdown(f"**Família:** {summary['family']}")
        st.markdown(f"**Faces:** {face_histogram_text(model)}")
        st.markdown(f"**Dual esperado:** {expected_dual_name(model)}")
        if summary.get("note"):
            st.warning(summary["note"])
        st.markdown("**Explicação automática**")
        st.write(automatic_explanation(model))


def render_lab(model, controls: dict[str, object]) -> None:
    summary = model.summary()
    dual = build_dual_graph(model)
    reliability, _ = reliability_tag(model)
    render_metrics(model, dual)
    mode_info = decomposition_info(model, str(controls.get("decomposition_mode", "Pirâmides face-centro")))
    st.markdown(f"**Família:** {summary['family']}  ·  **Confiabilidade:** `{reliability}`  ·  **Dual esperado:** `{expected_dual_name(model)}`  ·  **Modo:** `{mode_info.mode}`")
    st.caption(mode_info.description)
    if mode_info.warning:
        st.info(mode_info.warning)
    if summary.get("note"):
        st.warning(summary["note"])
    options = default_render_options(**controls)
    fig = build_figure(model, options)
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False, "scrollZoom": True})
    if controls.get("silent_mode"):
        st.caption("Modo silencioso ativo: legenda, rótulos e normais ficam ocultos para reduzir poluição visual.")
    elif controls.get("color_mode") == "Por peça" and len(model.faces) > 14:
        st.caption("Legenda adaptativa: em sólidos com muitas faces, a legenda por peça é ocultada e os detalhes ficam no hover.")
    if controls.get("show_dual") and not controls.get("dual_follow_explosion") and float(controls.get("explosion", 0.0)) > 0.30:
        st.warning("Dual fixo com explosão alta: o grafo dual permanece no sólido original e pode perder correspondência espacial com as peças. Use 'Dual acompanha explosão' para leitura face → vértice.")


def render_dual(model, controls: dict[str, object]) -> None:
    dual = build_dual_graph(model)
    summary = model.summary()
    st.subheader("Dual Explorer")
    st.write(duality_explanation(model))
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Dual esperado", expected_dual_name(model))
    k2.metric("Vértices do dual", len(dual.vertices))
    k3.metric("Arestas do dual", len(dual.edges))
    k4.metric("Faces estimadas do dual", summary["vertices"])

    st.markdown("#### Comparação sólido × dual")
    st.dataframe(dual_comparison_rows(model), hide_index=True, width="stretch")

    st.markdown("#### Comparação lado a lado")
    col_original, col_dual = st.columns(2, gap="large")
    with col_original:
        st.caption("Sólido original")
        original_fig = build_figure(
            model,
            default_render_options(
                explosion=0.0,
                face_filter="Todas",
                color_mode=str(controls["color_mode"]),
                show_ghost=False,
                show_dual=False,
                show_edges=True,
                show_center=True,
                silent_mode=bool(controls["silent_mode"]),
                height=560,
            ),
        )
        st.plotly_chart(original_fig, width="stretch", config={"displaylogo": False, "scrollZoom": True})
    with col_dual:
        st.caption("Dual visual por centros de faces")
        dual_fig = build_dual_only_figure(model, progress=float(controls["dual_progress"]), height=560)
        st.plotly_chart(dual_fig, width="stretch", config={"displaylogo": False, "scrollZoom": True})

    st.markdown("#### Animação guiada da dualidade")
    if controls.get("dual_follow_explosion"):
        st.caption("Modo atual: o dual acompanha a explosão das faces/pirâmides, preservando a correspondência face → vértice dual.")
    else:
        st.caption("Modo atual: dual fixo no sólido original. É útil para ver a estrutura interna, mas perde alinhamento espacial quando o afastamento é alto.")
    step_options = guided_duality_steps(model)
    selected_step_index = st.slider("Etapa didática", min_value=1, max_value=len(step_options), value=len(step_options), step=1) - 1
    selected_step = step_options[selected_step_index]
    st.markdown(dual_step_html(selected_step.etapa, selected_step.titulo, selected_step.descricao), unsafe_allow_html=True)
    guided_fig = build_figure(
        model,
        default_render_options(
            explosion=0.15,
            face_filter="Todas",
            color_mode=str(controls["color_mode"]),
            show_ghost=True,
            show_dual=True,
            dual_progress=selected_step.progresso,
            dual_follow_explosion=bool(controls.get("dual_follow_explosion", True)),
            show_edges=True,
            show_center=True,
            silent_mode=bool(controls["silent_mode"]),
            height=620,
        ),
    )
    st.plotly_chart(guided_fig, width="stretch", config={"displaylogo": False, "scrollZoom": True})
    with st.expander("Abrir animação Plotly com botão Play"):
        animated_fig = build_duality_animation_figure(
            model,
            default_render_options(
                explosion=0.15,
                color_mode=str(controls["color_mode"]),
                show_ghost=True,
                show_dual=True,
                dual_follow_explosion=bool(controls.get("dual_follow_explosion", True)),
                show_edges=True,
                show_center=True,
                silent_mode=bool(controls["silent_mode"]),
                height=680,
            ),
            steps=9,
        )
        st.plotly_chart(animated_fig, width="stretch", config={"displaylogo": False, "scrollZoom": True})
    st.markdown("#### Roteiro da animação")
    st.dataframe(guided_duality_rows(model), hide_index=True, width="stretch")


def render_lesson(model, lesson_level: str) -> None:
    st.subheader("Aula guiada")
    profile = level_profile(lesson_level)
    st.markdown(f"### {profile.level} — {profile.audience}")
    st.write(f"**Foco:** {profile.focus}")

    obj_cols = st.columns([1.1, 0.9], gap="large")
    with obj_cols[0]:
        st.markdown("#### Objetivos da atividade")
        for obj in profile.objectives:
            st.markdown(f"- {obj}")
    with obj_cols[1]:
        st.markdown("#### Vocabulário-chave")
        st.write(", ".join(profile.vocabulary))
        st.info("Sequência: observar → contar V/E/F → explodir por faces → identificar peças → comparar dual → responder questões.")

    st.markdown("#### Sequência didática guiada")
    sequence_rows = guided_sequence(model, lesson_level)
    selected_lesson_step = st.slider("Etapa da sequência", min_value=1, max_value=len(sequence_rows), value=1, step=1)
    st.markdown(lesson_step_html(sequence_rows[selected_lesson_step - 1]), unsafe_allow_html=True)
    st.dataframe(sequence_rows, hide_index=True, width="stretch")

    st.markdown("#### Perguntas automáticas com gabarito")
    questions = lesson_questions(model, lesson_level)
    st.dataframe(questions, hide_index=True, width="stretch")

    st.markdown("#### Modo professor")
    st.dataframe(teacher_questions(model), hide_index=True, width="stretch")
    with st.expander("Texto curto para abertura/fechamento"):
        summary = model.summary()
        st.write(
            f"Abertura: vamos desmontar virtualmente o {model.name}. Suas {summary['faces']} faces geram {summary['faces']} pirâmides, "
            "ajudando a compreender volume, área, dualidade e característica de Euler."
        )
        st.write(
            "Fechamento: compare o sólido explodido com o sólido montado e explique por que faces do original viram vértices do dual."
        )

    activity_html = build_lesson_html(model, lesson_level)
    activity_txt = build_lesson_text(model, lesson_level)
    activity_json = lesson_json(model, lesson_level)
    slug = safe_file_slug(model.name)
    b1, b2, b3 = st.columns(3)
    b1.download_button("Baixar atividade HTML", activity_html, file_name=f"polyexplode_{slug}_atividade_{lesson_level.lower()}_v0_7_2.html", mime="text/html", width="stretch")
    b2.download_button("Baixar atividade TXT", activity_txt, file_name=f"polyexplode_{slug}_atividade_{lesson_level.lower()}_v0_7_2.txt", mime="text/plain", width="stretch")
    b3.download_button("Baixar atividade JSON", activity_json, file_name=f"polyexplode_{slug}_atividade_{lesson_level.lower()}_v0_7_2.json", mime="application/json", width="stretch")
    st.caption("A prévia HTML embutida foi removida nesta versão para reduzir duplicação visual; use o download para revisar o material completo.")


def render_anatomy(model) -> None:
    st.subheader("Anatomia didática do sólido")
    st.write(automatic_explanation(model))
    col_a, col_b = st.columns([0.9, 1.1], gap="large")
    with col_a:
        st.markdown("#### Histograma de faces")
        st.dataframe(face_rows(model), hide_index=True, width="stretch")
        st.markdown("#### Resumo técnico")
        st.json(model.summary(), expanded=False)
    with col_b:
        st.markdown("#### Tabela das peças")
        rows = piece_rows(model)
        st.dataframe(rows, hide_index=True, width="stretch")
        st.caption("Cada linha é uma pirâmide: base = face original; ápice = centro do sólido.")
    total_piece_volume = sum(row["Volume da peça"] for row in piece_rows(model))
    st.success(f"Soma dos volumes das peças: {total_piece_volume:.6f}")


def render_import() -> tuple[object | None, MeshValidationReport | None]:
    st.subheader("Importação OFF/JSON")
    st.markdown(
        "Esta página valida arquivos importados antes de tratá-los como sólidos ativos. "
        "O upload não substitui silenciosamente o sólido do catálogo nas demais páginas."
    )
    uploaded_file = st.file_uploader("Upload .off ou .json", type=["off", "json"])
    import_report: MeshValidationReport | None = None
    imported_model = None
    if uploaded_file is not None:
        try:
            raw_text = uploaded_file.getvalue().decode("utf-8", errors="replace")
            imported = import_uploaded_solid(raw_text, uploaded_file.name)
            import_report = imported.report
            if imported.report.ok_to_build:
                imported_model = build_solid_from_definition(imported.definition)
                st.success(f"Usando importado nesta página: {imported_model.name}")
            else:
                st.error("O arquivo foi lido, mas contém erro crítico e não será usado como modelo ativo.")
        except Exception as exc:
            st.error(str(exc))

    if import_report is not None:
        st.markdown("#### Resultado da validação")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("V", import_report.vertex_count)
        m2.metric("F", import_report.face_count)
        m3.metric("E", import_report.edge_count)
        m4.metric("χ", import_report.euler)
        m5.metric("Convexidade", import_report.convexity)
        if import_report.ok_to_build and not import_report.has_warnings:
            st.success("Arquivo importado sem erros críticos ou avisos importantes.")
        elif import_report.ok_to_build:
            st.warning("Arquivo importado sem erro crítico, mas com avisos. Interprete volume/dualidade com cautela.")
        st.dataframe(validation_rows(import_report), hide_index=True, width="stretch")
        with st.expander("Relatório JSON de validação"):
            st.json(import_report.to_jsonable(), expanded=True)
        if imported_model is not None:
            st.markdown("#### Visualização do importado")
            st.plotly_chart(build_figure(imported_model, default_render_options(explosion=0.55, show_dual=True, height=620)), width="stretch", config={"displaylogo": False, "scrollZoom": True})
    else:
        st.info("Nenhum arquivo importado nesta sessão.")

    st.markdown("#### Formato JSON aceito")
    st.code(example_json_tetrahedron(), language="json")
    st.markdown("#### Exemplo OFF aceito")
    st.code(example_off_cube(), language="text")
    st.caption("Aviso: em sólidos não convexos, abertos, com faces cruzadas ou Euler diferente de 2, a explosão pode continuar útil visualmente, mas deixa de ser uma certificação volumétrica.")
    return imported_model, import_report


def render_report(model, controls: dict[str, object], lesson_level: str, import_report: MeshValidationReport | None = None) -> None:
    st.subheader("Relatório e downloads")
    manifest = manifest_json(model, import_report, lesson_level)
    html_report = merged_html_report(model, import_report, lesson_level)
    activity_html = build_lesson_html(model, lesson_level)
    activity_txt = build_lesson_text(model, lesson_level)
    slug = safe_file_slug(model.name)
    report_fig = build_figure(model, default_render_options(**controls))
    interactive_html = html_download(report_fig)
    animated_html = html_download(build_duality_animation_figure(model, default_render_options(explosion=0.15, color_mode=str(controls["color_mode"]), show_ghost=True, show_dual=True, dual_follow_explosion=bool(controls.get("dual_follow_explosion", True)), height=720), steps=9))

    d1, d2, d3 = st.columns(3)
    d1.download_button("Relatório HTML didático", html_report, file_name=f"polyexplode_{slug}_relatorio_didatico_v0_7_2.html", mime="text/html", width="stretch")
    d2.download_button("Manifesto JSON", manifest, file_name=f"polyexplode_{slug}_manifest_v0_7_2.json", mime="application/json", width="stretch")
    d3.download_button("Visualização HTML", interactive_html, file_name=f"polyexplode_{slug}_visualizacao_v0_7_2.html", mime="text/html", width="stretch")
    d4, d5, d6 = st.columns(3)
    d4.download_button("Animação dual HTML", animated_html, file_name=f"polyexplode_{slug}_dual_animacao_v0_7_2.html", mime="text/html", width="stretch")
    d5.download_button("Atividade HTML", activity_html, file_name=f"polyexplode_{slug}_atividade_{lesson_level.lower()}_v0_7_2.html", mime="text/html", width="stretch")
    d6.download_button("Atividade TXT", activity_txt, file_name=f"polyexplode_{slug}_atividade_{lesson_level.lower()}_v0_7_2.txt", mime="text/plain", width="stretch")
    tech_html = technical_report_html(model)
    st.download_button("Diagnóstico técnico HTML", tech_html, file_name=f"polyexplode_{slug}_diagnostico_tecnico_v0_7_2.html", mime="text/html", width="stretch")
    st.caption("A prévia HTML embutida foi removida para evitar duplicação de conteúdo na tela. Os arquivos completos continuam disponíveis para download.")
    with st.expander("Prévia curta do manifesto JSON"):
        st.code(manifest[:5000] + ("\n..." if len(manifest) > 5000 else ""), language="json")


def render_decomposition_modes(model, controls: dict[str, object]) -> None:
    st.subheader("Modos de decomposição")
    st.write("A v0.7.2 mantém os cinco modos de decomposição e acrescenta hardening para GitHub/Streamlit Cloud: casca por faces, volume por pirâmides, componentes conectados, camadas e entidades V/E/F.")
    selected_mode = st.selectbox("Modo para analisar", DECOMPOSITION_MODES, index=DECOMPOSITION_MODES.index(str(controls.get("decomposition_mode", "Pirâmides face-centro"))))
    info = decomposition_info(model, selected_mode)
    st.markdown(f"### {info.mode}")
    st.info(info.description)
    if info.warning:
        st.warning(info.warning)
    c1, c2, c3 = st.columns(3)
    c1.metric("Peças/grupos", info.piece_count)
    c2.metric("V", len(model.vertices))
    c3.metric("E/F", f"{model.edge_count}/{len(model.faces)}")
    if info.groups:
        st.markdown("**Grupos:** " + " · ".join(info.groups))
    st.dataframe(decomposition_rows(model, selected_mode), hide_index=True, width="stretch")
    local_controls = dict(controls)
    local_controls["decomposition_mode"] = selected_mode
    local_controls["show_dual"] = selected_mode in {"Pirâmides face-centro", "Faces", "Camadas"}
    local_controls["show_ghost"] = True
    fig = build_figure(model, default_render_options(**local_controls))
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False, "scrollZoom": True})
    st.caption("Em Componentes e V/E/F, o dual sobreposto fica desligado por padrão porque a leitura principal deixa de ser face → vértice dual.")


def render_diagnostics(model) -> None:
    st.subheader("Diagnóstico matemático")
    report = diagnose_model(model)
    cols = st.columns(6)
    cols[0].metric("Status", report.status)
    cols[1].metric("Normais externas", "OK" if report.outward_normals_ok else "falha")
    cols[2].metric("Planaridade máx.", f"{report.max_planarity_error:.2e}")
    cols[3].metric("Manifold", "sim" if report.closed_manifold else "não")
    cols[4].metric("Convexidade", report.convexity)
    cols[5].metric("χ", report.euler)

    if report.status == "ok":
        st.success("Diagnóstico técnico sem avisos para este modelo.")
    elif report.status == "experimental":
        st.warning("Modelo experimental auditado: útil para visualização, mas não para certificação formal.")
    elif report.status == "aviso":
        st.warning("O modelo é utilizável, mas há avisos técnicos. Interprete volume/dualidade com cautela.")
    else:
        st.error("Há falha crítica no diagnóstico técnico deste modelo.")

    st.markdown("#### Mensagens do diagnóstico")
    st.dataframe(report.message_rows(), hide_index=True, width="stretch")

    st.markdown("#### Faces: orientação, normais externas e planaridade")
    st.dataframe(face_diagnostic_rows(model), hide_index=True, width="stretch")

    st.markdown("#### Arestas: manifoldness")
    edge_rows = edge_diagnostic_rows(model)
    problem_edges = [row for row in edge_rows if row["Status"] != "OK"]
    if problem_edges:
        st.warning(f"Foram encontradas {len(problem_edges)} aresta(s) com multiplicidade diferente de 2.")
        st.dataframe(problem_edges, hide_index=True, width="stretch")
        with st.expander("Mostrar todas as arestas"):
            st.dataframe(edge_rows, hide_index=True, width="stretch")
    else:
        st.success("Todas as arestas têm multiplicidade 2.")
        with st.expander("Mostrar tabela completa de arestas"):
            st.dataframe(edge_rows, hide_index=True, width="stretch")

    st.markdown("#### Convexidade por planos de suporte")
    convex_rows = convexity_diagnostic_rows(model)
    convex_problem = [row for row in convex_rows if int(row["Violações"]) > 0]
    if convex_problem:
        st.warning(f"Há {len(convex_problem)} face(s) que não se comportam como plano de suporte perfeito.")
        st.dataframe(convex_problem, hide_index=True, width="stretch")
        with st.expander("Mostrar todas as faces no teste de convexidade"):
            st.dataframe(convex_rows, hide_index=True, width="stretch")
    else:
        st.success("Todas as faces passaram no teste de semiespaço: convexidade provável.")
        with st.expander("Mostrar tabela completa de convexidade"):
            st.dataframe(convex_rows, hide_index=True, width="stretch")

    html = technical_report_html(model)
    st.download_button(
        "Baixar relatório técnico HTML",
        html,
        file_name=f"polyexplode_{safe_file_slug(model.name)}_diagnostico_tecnico_v0_7_2.html",
        mime="text/html",
        width="stretch",
    )


def render_catalog() -> None:
    st.subheader("Catálogo e validação interna")
    metadata = cached_catalog_metadata()
    counts = Counter(item["family"] for item in metadata.values())
    rows = [{"Família": family, "Sólidos": count} for family, count in sorted(counts.items())]
    st.dataframe(rows, hide_index=True, width="stretch")
    st.markdown(f"**Total:** {len(SOLID_NAMES)} sólidos · **Experimentais auditados:** {len(EXPERIMENTAL_SOLID_NAMES)}")

    st.markdown("#### Validação interna do catálogo renderizado")
    validation = cached_catalog_validation_rows()
    st.dataframe(validation, hide_index=True, width="stretch")
    problematic = [row for row in validation if row["Status"] in {"crítico", "atenção"}]
    experimental = [row for row in validation if row["Status"] == "experimental"]
    if problematic:
        st.error(f"Há {len(problematic)} modelo(s) não experimental(is) com problema de validação.")
    else:
        st.success("Nenhum modelo não experimental falhou em manifoldness/Euler na validação interna.")
    if experimental:
        st.warning("J6/J10 foram preservados no catálogo como experimentais, com aviso explícito de malha problemática.")

    st.markdown("#### Diagnóstico técnico resumido v0.6")
    diagnostic_rows = cached_catalog_diagnostic_rows()
    st.dataframe(diagnostic_rows, hide_index=True, width="stretch")

    st.markdown("#### Etiquetas de confiabilidade e dualidade")
    reliability_rows = []
    for name in SOLID_NAMES:
        m = load_model(name)
        tag, note = reliability_tag(m)
        d = build_dual_graph(m)
        reliability_rows.append({
            "Sólido": name,
            "Família": m.family,
            "Confiabilidade": tag,
            "Dual esperado/visual": expected_dual_name(m),
            "Vértices dual": len(d.vertices),
            "Arestas dual": len(d.edges),
            "Nota": m.note or note,
        })
    st.dataframe(reliability_rows, hide_index=True, width="stretch")


def main() -> None:
    st.title(f"💥 PolyExplode Streamlit v{__version__}")
    st.caption("Cloud Hardening — app preparado para repositório público, CI e Streamlit Cloud. Sem STL.")

    metadata = cached_catalog_metadata()
    families = ["Todas"] + sorted({item["family"] for item in metadata.values()})
    pages = [
        "Início",
        "Laboratório 3D",
        "Dual Explorer",
        "Aula guiada",
        "Anatomia",
        "Importação",
        "Relatório/downloads",
        "Modos de decomposição",
        "Diagnóstico matemático",
        "Catálogo/validação",
    ]

    with st.sidebar:
        st.header("Navegação")
        page = st.radio("Área de trabalho", pages, index=0)
        st.divider()
        st.header("Catálogo")
        selected_family = st.selectbox("Família", families, index=0)
        names = family_filtered_names(selected_family)
        default_index = names.index("Dodecaedro") if "Dodecaedro" in names else 0
        selected_solid = st.selectbox("Sólido", names, index=default_index)

    model = load_model(selected_solid)
    controls = {
        "explosion": 0.70,
        "face_filter": "Todas",
        "color_mode": "Por tipo de face",
        "decomposition_mode": "Pirâmides face-centro",
        "show_ghost": True,
        "show_dual": True,
        "dual_progress": 1.0,
        "dual_follow_explosion": True,
        "show_edges": True,
        "show_center": True,
        "show_normals": False,
        "show_labels": False,
        "silent_mode": False,
        "height": 720,
    }
    lesson_level = "Médio"

    if page in {"Laboratório 3D", "Dual Explorer", "Relatório/downloads"}:
        with st.sidebar:
            st.divider()
            st.header("Visualização")
            controls["silent_mode"] = st.checkbox("Modo silencioso", value=False, help="Oculta legenda, rótulos e normais para reduzir poluição visual.")
            controls["decomposition_mode"] = st.selectbox("Modo de decomposição", DECOMPOSITION_MODES, index=0)
            controls["face_filter"] = st.selectbox("Explodir faces", face_filter_options(model), index=0)
            controls["explosion"] = st.slider("Afastamento", min_value=0.0, max_value=2.2, value=0.70, step=0.05)
            controls["color_mode"] = st.radio("Cores", ["Por tipo de face", "Por peça"], horizontal=False)
            st.divider()
            st.header("Dualidade")
            controls["show_dual"] = st.checkbox("Mostrar dual visual", value=True)
            controls["dual_progress"] = st.slider("Progresso do dual", min_value=0.0, max_value=1.0, value=1.0, step=0.05)
            controls["dual_follow_explosion"] = st.checkbox("Dual acompanha explosão", value=True, help="Quando ligado, cada vértice dual recebe o mesmo deslocamento da face/pirâmide correspondente.")
            if controls["show_dual"] and not controls["dual_follow_explosion"] and float(controls["explosion"]) > 0.30:
                st.caption("Aviso: dual fixo com afastamento alto pode parecer desconectado das peças.")
            st.divider()
            st.header("Elementos")
            controls["show_ghost"] = st.checkbox("Casca fantasma original", value=True)
            controls["show_edges"] = st.checkbox("Arestas", value=True)
            controls["show_center"] = st.checkbox("Centro", value=True)
            if not controls["silent_mode"]:
                controls["show_normals"] = st.checkbox("Normais externas", value=False)
                controls["show_labels"] = st.checkbox("Rótulos das faces", value=False)
            controls["height"] = st.slider("Altura do visualizador", min_value=520, max_value=920, value=720, step=20)

    if page in {"Aula guiada", "Relatório/downloads", "Início"}:
        with st.sidebar:
            st.divider()
            st.header("Aula guiada")
            lesson_level = st.selectbox("Nível da atividade", LESSON_LEVELS, index=1)

    if page == "Início":
        render_home(model, lesson_level)
    elif page == "Laboratório 3D":
        render_lab(model, controls)
    elif page == "Dual Explorer":
        render_dual(model, controls)
    elif page == "Aula guiada":
        render_lesson(model, lesson_level)
    elif page == "Anatomia":
        render_anatomy(model)
    elif page == "Importação":
        render_import()
    elif page == "Relatório/downloads":
        render_report(model, controls, lesson_level)
    elif page == "Modos de decomposição":
        render_decomposition_modes(model, controls)
    elif page == "Diagnóstico matemático":
        render_diagnostics(model)
    elif page == "Catálogo/validação":
        render_catalog()


if __name__ == "__main__":
    main()
