from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

NODE_STYLE = {
    "source": {
        "fillcolor": "lightyellow",
        "shape": "box",
    },
    "intermediate": {
        "fillcolor": "lightblue",
        "shape": "ellipse",
    },
    "final": {
        "fillcolor": "lightgreen",
        "shape": "box",
    },
    "unknown": {
        "fillcolor": "lightgray",
        "shape": "ellipse",
    },
}


def ensure_output_dir(output_path: str | Path) -> Path:
    """
    Ensure the output directory exists and return the resolved file path.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_node_style(node_type: str) -> dict:
    """
    Return styling information for a node type.
    """
    return NODE_STYLE.get(node_type, NODE_STYLE["unknown"])


def render_dag_graphviz(graph: nx.DiGraph, output_path: str | Path) -> Path:
    """
    Render a DAG using Graphviz and save as PNG.

    Requires the Python graphviz package and the Graphviz system executable.
    """
    try:
        from graphviz import Digraph
    except ImportError as exc:
        raise RuntimeError("Graphviz Python package is not installed.") from exc

    output_path = ensure_output_dir(output_path)
    output_stem = output_path.with_suffix("")

    dot = Digraph(comment="Data Pipeline DAG", format="png")
    dot.attr(rankdir="LR")
    dot.attr("node", style="filled", fontname="Helvetica", fontsize="10")
    dot.attr("edge", fontname="Helvetica", fontsize="9")

    for node, attrs in graph.nodes(data=True):
        node_type = attrs.get("node_type", "unknown")
        style = get_node_style(node_type)

        dot.node(
            name=node,
            label=node,
            fillcolor=style["fillcolor"],
            shape=style["shape"],
        )

    for source, target in graph.edges():
        dot.edge(source, target)

    try:
        rendered_path = dot.render(filename=str(output_stem), cleanup=True)
    except Exception as exc:
        raise RuntimeError(
            "Graphviz rendering failed. Ensure Graphviz is installed and available on PATH."
        ) from exc

    return Path(rendered_path)


def render_dag_networkx(graph: nx.DiGraph, output_path: str | Path) -> Path:
    """
    Render a DAG using networkx + matplotlib and save as PNG.

    This serves as a fallback when Graphviz is unavailable.
    """
    output_path = ensure_output_dir(output_path)

    plt.figure(figsize=(12, 8))

    try:
        pos = nx.nx_agraph.graphviz_layout(graph, prog="dot")
    except Exception:
        try:
            pos = nx.nx_pydot.graphviz_layout(graph, prog="dot")
        except Exception:
            pos = nx.spring_layout(graph, seed=42)

    source_nodes = []
    intermediate_nodes = []
    final_nodes = []
    unknown_nodes = []

    for node, attrs in graph.nodes(data=True):
        node_type = attrs.get("node_type", "unknown")
        if node_type == "source":
            source_nodes.append(node)
        elif node_type == "intermediate":
            intermediate_nodes.append(node)
        elif node_type == "final":
            final_nodes.append(node)
        else:
            unknown_nodes.append(node)

    nx.draw_networkx_edges(graph, pos, arrows=True, arrowstyle="->", arrowsize=18)

    if source_nodes:
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=source_nodes,
            node_shape="s",
            node_color="lightyellow",
            node_size=2200,
        )

    if intermediate_nodes:
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=intermediate_nodes,
            node_shape="o",
            node_color="lightblue",
            node_size=2200,
        )

    if final_nodes:
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=final_nodes,
            node_shape="s",
            node_color="lightgreen",
            node_size=2400,
        )

    if unknown_nodes:
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=unknown_nodes,
            node_shape="o",
            node_color="lightgray",
            node_size=2200,
        )

    nx.draw_networkx_labels(graph, pos, font_size=9)

    plt.title("Data Pipeline DAG")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()

    return output_path


def render_dag(
    graph: nx.DiGraph,
    output_path: str | Path = "output/pipeline_dag.png",
    engine: str = "auto",
) -> Path:
    """
    Render a DAG to an image file.

    engine:
    - auto: try Graphviz first, then fallback to networkx
    - graphviz: force Graphviz
    - networkx: force networkx + matplotlib
    """
    if engine == "graphviz":
        return render_dag_graphviz(graph, output_path)

    if engine == "networkx":
        return render_dag_networkx(graph, output_path)

    if engine == "auto":
        try:
            return render_dag_graphviz(graph, output_path)
        except Exception:
            return render_dag_networkx(graph, output_path)

    raise ValueError(f"Unsupported engine: {engine}")
