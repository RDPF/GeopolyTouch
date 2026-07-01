from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import plotly.graph_objects as go

from .core import (
    SolidModel,
    build_dual_graph,
    exploded_piece_vertices,
    face_matches_filter,
    face_type_name,
)
from .decomposition import (
    DECOMPOSITION_MODES,
    connected_face_components,
    edge_pairs,
    face_layer,
    layer_multiplier,
)


FACE_TYPE_COLORS = {
    3: "#4C78A8",   # triângulos
    4: "#F58518",   # quadriláteros
    5: "#54A24B",   # pentágonos
    6: "#E45756",   # hexágonos
    8: "#72B7B2",   # octógonos
    10: "#B279A2",  # decágonos
}
PIECE_COLORS = [
    "#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#B279A2",
    "#FF9DA6", "#9D755D", "#BAB0AC", "#8CD17D", "#B6992D", "#499894",
    "#D37295", "#FABFD2", "#86BCB6", "#F1CE63", "#79706E", "#D4A6C8",
]


@dataclass(frozen=True)
class RenderOptions:
    explosion: float = 0.0
    face_filter: str = "Todas"
    color_mode: str = "Por tipo de face"
    decomposition_mode: str = "Pirâmides face-centro"
    show_ghost: bool = True
    show_dual: bool = False
    dual_progress: float = 1.0
    dual_follow_explosion: bool = True
    show_edges: bool = True
    show_center: bool = True
    show_normals: bool = False
    show_labels: bool = False
    silent_mode: bool = False
    adaptive_legend: bool = True
    legend_threshold: int = 14
    height: int = 720


def _fan_triangulation(n: int, offset: int = 0, reverse: bool = False) -> list[tuple[int, int, int]]:
    """Triangulate an n-gon indexed offset..offset+n-1 using a simple fan."""
    tris: list[tuple[int, int, int]] = []
    for k in range(1, n - 1):
        tri = (offset, offset + k, offset + k + 1)
        if reverse:
            tri = (tri[0], tri[2], tri[1])
        tris.append(tri)
    return tris


def _face_color(sides: int, face_index: int, color_mode: str) -> str:
    if color_mode == "Por peça":
        return PIECE_COLORS[face_index % len(PIECE_COLORS)]
    return FACE_TYPE_COLORS.get(int(sides), PIECE_COLORS[face_index % len(PIECE_COLORS)])


def _add_mesh_trace(fig: go.Figure, points: np.ndarray, triangles: Iterable[tuple[int, int, int]], *, color: str, name: str, opacity: float, showlegend: bool = False, hovertext: str | None = None) -> None:
    pts = np.asarray(points, dtype=float)
    tris = list(triangles)
    if len(pts) == 0 or len(tris) == 0:
        return
    i, j, k = zip(*tris)
    fig.add_trace(go.Mesh3d(
        x=pts[:, 0], y=pts[:, 1], z=pts[:, 2],
        i=list(i), j=list(j), k=list(k),
        color=color,
        opacity=float(opacity),
        name=name,
        flatshading=True,
        showscale=False,
        showlegend=showlegend,
        hoverinfo="text" if hovertext else "skip",
        text=[hovertext or name] * len(pts),
    ))


def _edge_segments_for_piece(base: np.ndarray, apex: np.ndarray | None = None) -> tuple[list[float], list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []

    def add_segment(a: np.ndarray, b: np.ndarray) -> None:
        xs.extend([float(a[0]), float(b[0]), None])
        ys.extend([float(a[1]), float(b[1]), None])
        zs.extend([float(a[2]), float(b[2]), None])

    n = len(base)
    for idx in range(n):
        add_segment(base[idx], base[(idx + 1) % n])
        if apex is not None:
            add_segment(apex, base[idx])
    return xs, ys, zs


def _normal_segments(model: SolidModel, explosion: float, face_filter: str) -> tuple[list[float], list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []

    for face in model.faces:
        active = face_matches_filter(face, face_filter)
        local_explosion = explosion if active else 0.0
        _base, _apex, shift = exploded_piece_vertices(model, face, local_explosion)
        start = face.center + shift
        end = start + face.normal * model.radius * 0.22
        xs.extend([float(start[0]), float(end[0]), None])
        ys.extend([float(start[1]), float(end[1]), None])
        zs.extend([float(start[2]), float(end[2]), None])
    return xs, ys, zs


def _ghost_mesh(model: SolidModel) -> tuple[np.ndarray, list[tuple[int, int, int]]]:
    points: list[np.ndarray] = []
    triangles: list[tuple[int, int, int]] = []
    for face in model.faces:
        pts = model.vertices[face.indices]
        start = len(points)
        points.extend([np.asarray(p, dtype=float) for p in pts])
        triangles.extend(_fan_triangulation(len(pts), start))
    return np.array(points, dtype=float), triangles


def _legend_name(face_sides: int, face_index: int, color_mode: str, prefix: str = "") -> str:
    if color_mode == "Por tipo de face":
        return f"{prefix}{face_type_name(face_sides)}"
    return f"{prefix}Peça {face_index + 1:02d}"


def _add_pyramid_piece(fig: go.Figure, model: SolidModel, face_index: int, face, local_explosion: float, color_mode: str, effective_show_legend: bool, legend_seen: set[str], edge_buffers: tuple[list[float], list[float], list[float]], *, label_prefix: str = "") -> None:
    base, apex, _shift = exploded_piece_vertices(model, face, local_explosion)
    points = np.vstack([apex.reshape(1, 3), base])
    n = len(base)
    side_triangles = [(0, j + 1, ((j + 1) % n) + 1) for j in range(n)]
    base_triangles = _fan_triangulation(n, 1, reverse=True)
    color = _face_color(face.sides, face_index, color_mode)
    legend_name = _legend_name(face.sides, face_index, color_mode, label_prefix)
    showlegend = effective_show_legend and legend_name not in legend_seen
    legend_seen.add(legend_name)
    hover = (
        f"Peça {face_index + 1}<br>"
        f"Modo: pirâmide face-centro<br>"
        f"Base: {face_type_name(face.sides)}<br>"
        f"Área da base: {face.area:.5f}<br>"
        f"Altura ao centro: {face.distance_to_center:.5f}<br>"
        f"Volume da peça: {face.area * face.distance_to_center / 3.0:.5f}"
    )
    _add_mesh_trace(fig, points, side_triangles + base_triangles, color=color, name=legend_name, opacity=0.78, showlegend=showlegend, hovertext=hover)
    xs, ys, zs = _edge_segments_for_piece(base, apex)
    edge_buffers[0].extend(xs); edge_buffers[1].extend(ys); edge_buffers[2].extend(zs)


def _add_face_plate(fig: go.Figure, model: SolidModel, face_index: int, face, local_explosion: float, color_mode: str, effective_show_legend: bool, legend_seen: set[str], edge_buffers: tuple[list[float], list[float], list[float]], *, label_prefix: str = "") -> np.ndarray:
    shift = face.normal * float(local_explosion) * model.radius
    pts = model.vertices[face.indices] + shift
    triangles = _fan_triangulation(len(pts), 0)
    color = _face_color(face.sides, face_index, color_mode)
    legend_name = _legend_name(face.sides, face_index, color_mode, label_prefix)
    showlegend = effective_show_legend and legend_name not in legend_seen
    legend_seen.add(legend_name)
    hover = (
        f"Face {face_index + 1}<br>"
        f"Modo: face/placa<br>"
        f"Tipo: {face_type_name(face.sides)}<br>"
        f"Área: {face.area:.5f}"
    )
    _add_mesh_trace(fig, pts, triangles, color=color, name=legend_name, opacity=0.82, showlegend=showlegend, hovertext=hover)
    xs, ys, zs = _edge_segments_for_piece(pts, None)
    edge_buffers[0].extend(xs); edge_buffers[1].extend(ys); edge_buffers[2].extend(zs)
    return pts


def _add_topological_mode(fig: go.Figure, model: SolidModel, options: RenderOptions, effective_show_legend: bool) -> None:
    # Faces move along normals, edges move radially by their midpoint, vertices move radially from the center.
    face_edge_x: list[float] = []
    face_edge_y: list[float] = []
    face_edge_z: list[float] = []
    legend_seen: set[str] = set()
    for idx, face in enumerate(model.faces):
        active = face_matches_filter(face, options.face_filter)
        local_explosion = options.explosion * 0.75 if active else 0.0
        _add_face_plate(
            fig, model, idx, face, local_explosion, options.color_mode,
            effective_show_legend, legend_seen, (face_edge_x, face_edge_y, face_edge_z),
            label_prefix="Faces: ",
        )
    if options.show_edges and face_edge_x:
        fig.add_trace(go.Scatter3d(
            x=face_edge_x, y=face_edge_y, z=face_edge_z,
            mode="lines", line=dict(color="#111111", width=1.5),
            name="Contornos das faces", showlegend=effective_show_legend, hoverinfo="skip",
        ))

    vx = []
    vy = []
    vz = []
    for vertex in model.vertices:
        direction = vertex - model.center
        norm = np.linalg.norm(direction)
        if norm > 1e-9:
            direction = direction / norm
        shifted = vertex + direction * float(options.explosion) * model.radius * 1.05
        vx.append(float(shifted[0])); vy.append(float(shifted[1])); vz.append(float(shifted[2]))
    fig.add_trace(go.Scatter3d(
        x=vx, y=vy, z=vz,
        mode="markers",
        marker=dict(size=5, color="#000000", opacity=0.85),
        name="Vértices separados",
        showlegend=effective_show_legend,
        hovertemplate="Vértice separado<extra></extra>",
    ))

    ex: list[float] = []
    ey: list[float] = []
    ez: list[float] = []
    for a, b in edge_pairs(model):
        pa = model.vertices[a]
        pb = model.vertices[b]
        midpoint = (pa + pb) / 2.0
        direction = midpoint - model.center
        norm = np.linalg.norm(direction)
        if norm > 1e-9:
            direction = direction / norm
        shift = direction * float(options.explosion) * model.radius * 0.45
        sa = pa + shift
        sb = pb + shift
        ex.extend([float(sa[0]), float(sb[0]), None])
        ey.extend([float(sa[1]), float(sb[1]), None])
        ez.extend([float(sa[2]), float(sb[2]), None])
    fig.add_trace(go.Scatter3d(
        x=ex, y=ey, z=ez,
        mode="lines",
        line=dict(color="#334155", width=5),
        name="Arestas separadas",
        showlegend=effective_show_legend,
        hoverinfo="skip",
    ))


def _component_direction(model: SolidModel, component_index: int, component_faces: list[int], component_count: int) -> np.ndarray:
    if component_count == 1:
        return np.zeros(3)
    centers = np.array([model.faces[i].center for i in component_faces], dtype=float)
    direction = centers.mean(axis=0) - model.center
    norm = np.linalg.norm(direction)
    if norm <= 1e-9:
        angle = 2 * np.pi * component_index / max(1, component_count)
        direction = np.array([np.cos(angle), np.sin(angle), 0.25], dtype=float)
        norm = np.linalg.norm(direction)
    return direction / norm


def _add_main_decomposition(fig: go.Figure, model: SolidModel, options: RenderOptions, effective_show_legend: bool, effective_show_labels: bool) -> tuple[list[float], list[float], list[float]]:
    mode = options.decomposition_mode if options.decomposition_mode in DECOMPOSITION_MODES else "Pirâmides face-centro"
    edge_x: list[float] = []
    edge_y: list[float] = []
    edge_z: list[float] = []
    legend_seen: set[str] = set()

    if mode == "Vértices/arestas/faces":
        _add_topological_mode(fig, model, options, effective_show_legend)
        return edge_x, edge_y, edge_z

    if mode == "Componentes":
        components = connected_face_components(model)
        for comp_index, comp in enumerate(components):
            direction = _component_direction(model, comp_index, comp, len(components))
            comp_shift = direction * float(options.explosion) * model.radius
            for face_index in comp:
                face = model.faces[face_index]
                pts = model.vertices[face.indices] + comp_shift
                triangles = _fan_triangulation(len(pts), 0)
                color = _face_color(face.sides, face_index, options.color_mode)
                legend_name = f"Componente {comp_index + 1}" if options.color_mode == "Por tipo de face" else f"Comp. {comp_index + 1} · face {face_index + 1}"
                showlegend = effective_show_legend and legend_name not in legend_seen
                legend_seen.add(legend_name)
                _add_mesh_trace(
                    fig, pts, triangles,
                    color=color, name=legend_name, opacity=0.80, showlegend=showlegend,
                    hovertext=f"Componente {comp_index + 1}<br>Face {face_index + 1}<br>{face_type_name(face.sides)}",
                )
                if options.show_edges:
                    xs, ys, zs = _edge_segments_for_piece(pts, None)
                    edge_x.extend(xs); edge_y.extend(ys); edge_z.extend(zs)
        return edge_x, edge_y, edge_z

    for idx, face in enumerate(model.faces):
        active = face_matches_filter(face, options.face_filter)
        local_explosion = options.explosion if active else 0.0
        if mode == "Camadas":
            local_explosion *= layer_multiplier(face_layer(model, face))
        if mode == "Faces":
            base = _add_face_plate(fig, model, idx, face, local_explosion, options.color_mode, effective_show_legend, legend_seen, (edge_x, edge_y, edge_z))
            if effective_show_labels:
                label_pos = base.mean(axis=0) + face.normal * model.radius * 0.08
                fig.add_trace(go.Scatter3d(x=[label_pos[0]], y=[label_pos[1]], z=[label_pos[2]], mode="text", text=[str(idx + 1)], textfont=dict(size=12, color="#111111"), showlegend=False, hoverinfo="skip"))
        else:
            _add_pyramid_piece(fig, model, idx, face, local_explosion, options.color_mode, effective_show_legend, legend_seen, (edge_x, edge_y, edge_z), label_prefix="Camadas: " if mode == "Camadas" else "")
            if effective_show_labels:
                base, _apex, _shift = exploded_piece_vertices(model, face, local_explosion)
                label_pos = base.mean(axis=0) + face.normal * model.radius * 0.08
                fig.add_trace(go.Scatter3d(x=[label_pos[0]], y=[label_pos[1]], z=[label_pos[2]], mode="text", text=[str(idx + 1)], textfont=dict(size=12, color="#111111"), showlegend=False, hoverinfo="skip"))
    return edge_x, edge_y, edge_z


def build_figure(model: SolidModel, options: RenderOptions | None = None) -> go.Figure:
    options = options or RenderOptions()
    fig = go.Figure()

    effective_show_labels = bool(options.show_labels and not options.silent_mode)
    effective_show_normals = bool(options.show_normals and not options.silent_mode)
    effective_show_legend = not bool(options.silent_mode)
    if options.adaptive_legend and options.color_mode == "Por peça" and len(model.faces) > int(options.legend_threshold):
        effective_show_legend = False

    if options.show_ghost:
        ghost_points, ghost_triangles = _ghost_mesh(model)
        _add_mesh_trace(
            fig,
            ghost_points,
            ghost_triangles,
            color="#7f7f7f",
            name="Casca original",
            opacity=0.12,
            showlegend=effective_show_legend,
            hovertext="Casca fantasma do sólido original",
        )

    edge_x, edge_y, edge_z = _add_main_decomposition(fig, model, options, effective_show_legend, effective_show_labels)

    if options.show_edges and edge_x:
        edge_name = "Arestas das peças" if options.decomposition_mode != "Faces" else "Arestas das faces"
        fig.add_trace(go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            mode="lines",
            line=dict(color="#111111", width=2),
            name=edge_name,
            showlegend=effective_show_legend,
            hoverinfo="skip",
        ))

    if options.show_dual:
        progress = max(0.0, min(1.0, float(options.dual_progress)))
        # The visual dual is anchored to face/pyramid modes. For component and V/E/F modes,
        # keep the fixed internal dual to avoid implying component-level duality.
        dual_can_follow = options.dual_follow_explosion and options.decomposition_mode in {"Pirâmides face-centro", "Faces", "Camadas"}
        dual = build_dual_graph(
            model,
            outward_scale=1.07 * progress,
            explosion=options.explosion,
            face_filter=options.face_filter,
            follow_explosion=dual_can_follow,
            progress=progress,
        )
        dx: list[float] = []
        dy: list[float] = []
        dz: list[float] = []
        for a, b in dual.edges:
            pa = dual.vertices[a]
            pb = dual.vertices[b]
            dx.extend([float(pa[0]), float(pb[0]), None])
            dy.extend([float(pa[1]), float(pb[1]), None])
            dz.extend([float(pa[2]), float(pb[2]), None])
        dual_opacity = max(0.08, min(0.95, 0.12 + 0.83 * progress))
        if len(dual.vertices):
            fig.add_trace(go.Scatter3d(
                x=dual.vertices[:, 0], y=dual.vertices[:, 1], z=dual.vertices[:, 2],
                mode="markers",
                marker=dict(size=5 + 3 * progress, color="#000000", opacity=dual_opacity),
                name="Vértices do dual",
                showlegend=effective_show_legend,
                hovertemplate="Centro de face / vértice do dual<extra></extra>",
            ))
        if dx:
            fig.add_trace(go.Scatter3d(
                x=dx, y=dy, z=dz,
                mode="lines",
                line=dict(color="#000000", width=max(1, 4 * progress)),
                opacity=dual_opacity,
                name="Arestas do dual",
                showlegend=effective_show_legend,
                hoverinfo="skip",
            ))

    if options.show_center:
        c = model.center
        fig.add_trace(go.Scatter3d(
            x=[c[0]], y=[c[1]], z=[c[2]],
            mode="markers",
            marker=dict(size=6, color="#000000", symbol="diamond"),
            name="Centro",
            showlegend=effective_show_legend,
            hovertemplate="Centro do sólido<extra></extra>",
        ))

    if effective_show_normals:
        nx, ny, nz = _normal_segments(model, options.explosion, options.face_filter)
        fig.add_trace(go.Scatter3d(
            x=nx, y=ny, z=nz,
            mode="lines",
            line=dict(color="#222222", width=5),
            name="Normais externas",
            showlegend=effective_show_legend,
            hoverinfo="skip",
        ))

    limit = model.radius * (1.0 + max(0.0, float(options.explosion)) * 1.35) + 0.65
    fig.update_layout(
        height=int(options.height),
        margin=dict(l=0, r=0, t=35, b=0),
        scene=dict(
            xaxis=dict(visible=False, range=[-limit, limit]),
            yaxis=dict(visible=False, range=[-limit, limit]),
            zaxis=dict(visible=False, range=[-limit, limit]),
            aspectmode="cube",
            bgcolor="rgba(0,0,0,0)",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=0.0, xanchor="center", x=0.5),
        showlegend=effective_show_legend,
        title=f"{model.name} — modo: {options.decomposition_mode}",
    )
    return fig


def _dual_segments(
    model: SolidModel,
    progress: float = 1.0,
    *,
    explosion: float = 0.0,
    face_filter: str = "Todas",
    follow_explosion: bool = False,
) -> tuple[np.ndarray, list[float], list[float], list[float]]:
    progress = max(0.0, min(1.0, float(progress)))
    dual = build_dual_graph(
        model,
        outward_scale=1.07 * progress,
        explosion=explosion,
        face_filter=face_filter,
        follow_explosion=follow_explosion,
        progress=progress,
    )
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for a, b in dual.edges:
        pa = dual.vertices[a]
        pb = dual.vertices[b]
        xs.extend([float(pa[0]), float(pb[0]), None])
        ys.extend([float(pa[1]), float(pb[1]), None])
        zs.extend([float(pa[2]), float(pb[2]), None])
    return dual.vertices, xs, ys, zs


def build_dual_only_figure(model: SolidModel, progress: float = 1.0, height: int = 560, title: str | None = None) -> go.Figure:
    """Render only the visual/combinatorial dual generated from face centers."""
    fig = go.Figure()
    vertices, xs, ys, zs = _dual_segments(model, progress)
    progress = max(0.0, min(1.0, float(progress)))
    opacity = max(0.08, min(0.96, 0.12 + 0.84 * progress))
    if xs:
        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode="lines",
            line=dict(color="#111111", width=max(1, 5 * progress)),
            opacity=opacity,
            name="Arestas do dual",
            hoverinfo="skip",
        ))
    if len(vertices):
        fig.add_trace(go.Scatter3d(
            x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2],
            mode="markers+text",
            marker=dict(size=6 + 3 * progress, color="#111111", opacity=opacity),
            text=[str(i + 1) for i in range(len(vertices))],
            textposition="top center",
            textfont=dict(size=10, color="#111111"),
            name="Centros das faces",
            hovertemplate="Vértice dual %{text}<extra></extra>",
        ))
    c = model.center
    fig.add_trace(go.Scatter3d(
        x=[c[0]], y=[c[1]], z=[c[2]],
        mode="markers",
        marker=dict(size=5, color="#777777", symbol="diamond"),
        name="Centro original",
        hovertemplate="Centro do sólido original<extra></extra>",
    ))
    limit = model.radius * 1.45 + 0.55
    fig.update_layout(
        height=int(height),
        margin=dict(l=0, r=0, t=35, b=0),
        scene=dict(
            xaxis=dict(visible=False, range=[-limit, limit]),
            yaxis=dict(visible=False, range=[-limit, limit]),
            zaxis=dict(visible=False, range=[-limit, limit]),
            aspectmode="cube",
            bgcolor="rgba(0,0,0,0)",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=0.0, xanchor="center", x=0.5),
        title=title or f"Dual visual de {model.name}",
    )
    return fig


def build_duality_animation_figure(model: SolidModel, base_options: RenderOptions | None = None, steps: int = 9) -> go.Figure:
    """Plotly figure with frames for a guided dual-emergence animation."""
    base_options = base_options or RenderOptions(show_dual=True, show_ghost=True, explosion=0.15)
    steps = max(3, int(steps))
    progress_values = np.linspace(0.0, 1.0, steps)
    figures = []
    for p in progress_values:
        options = RenderOptions(
            explosion=base_options.explosion,
            face_filter=base_options.face_filter,
            color_mode=base_options.color_mode,
            decomposition_mode=base_options.decomposition_mode,
            show_ghost=base_options.show_ghost,
            show_dual=True,
            dual_progress=float(p),
            dual_follow_explosion=base_options.dual_follow_explosion,
            show_edges=base_options.show_edges,
            show_center=base_options.show_center,
            show_normals=False,
            show_labels=False,
            height=base_options.height,
        )
        figures.append(build_figure(model, options))
    fig = figures[-1]
    fig.frames = [go.Frame(data=f.data, name=f"{p:.2f}") for f, p in zip(figures, progress_values)]
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                x=0.02,
                y=1.07,
                xanchor="left",
                yanchor="top",
                buttons=[
                    dict(
                        label="▶ Animar dual",
                        method="animate",
                        args=[None, {"frame": {"duration": 650, "redraw": True}, "fromcurrent": True, "transition": {"duration": 250}}],
                    ),
                    dict(
                        label="⏸ Pausar",
                        method="animate",
                        args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}}],
                    ),
                ],
            )
        ],
        sliders=[
            dict(
                active=len(progress_values) - 1,
                currentvalue={"prefix": "Progresso do dual: "},
                pad={"t": 45},
                steps=[
                    dict(
                        label=f"{p:.2f}",
                        method="animate",
                        args=[[f"{p:.2f}"], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}],
                    )
                    for p in progress_values
                ],
            )
        ],
        title=f"{model.name} — animação guiada da dualidade",
    )
    return fig
