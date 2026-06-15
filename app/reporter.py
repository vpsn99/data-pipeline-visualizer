from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import networkx as nx

from app.explainer import explain_full_pipeline
from app.graph_builder import export_graph_data, get_topological_order, graph_summary
from app.insights import explain_insights, summarize_insights
from app.model_classifier import summarize_layers

if TYPE_CHECKING:
    from app.sql_intelligence import SqlSemantics


def ensure_parent_dir(path: str | Path) -> Path:
    """
    Ensure the parent directory exists and return the Path object.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path


def generate_markdown_report(
    graph: nx.DiGraph,
    dag_image_path: str | Path | None = None,
    semantic_map: dict[str, SqlSemantics] | None = None,
) -> str:
    """
    Generate a Markdown report for the pipeline graph.
    """
    summary = graph_summary(graph)
    explanation = explain_full_pipeline(graph, semantic_map=semantic_map)

    sources_text = ", ".join(summary["sources"]) if summary["sources"] else "None"
    intermediates_text = ", ".join(summary["intermediates"]) if summary["intermediates"] else "None"
    finals_text = ", ".join(summary["finals"]) if summary["finals"] else "None"

    lines: list[str] = []
    lines.append("# Data Pipeline Report")
    lines.append("")

    lines.append("## Graph Summary")
    lines.append("")
    lines.append(f"- **Nodes:** {summary['num_nodes']}")
    lines.append(f"- **Edges:** {summary['num_edges']}")
    lines.append(f"- **Is DAG:** {summary['is_dag']}")
    lines.append(f"- **Sources:** {sources_text}")
    lines.append(f"- **Intermediates:** {intermediates_text}")
    lines.append(f"- **Finals:** {finals_text}")
    lines.append("")

    if summary["is_dag"]:
        topo_order = get_topological_order(graph)

        lines.append("## Topological Order")
        lines.append("")
        lines.append("```text")
        lines.extend(topo_order)
        lines.append("```")
        lines.append("")

    if dag_image_path is not None:
        dag_image = Path(dag_image_path).as_posix()

        lines.append("## Pipeline DAG")
        lines.append("")
        lines.append(f"![Pipeline DAG]({dag_image})")
        lines.append("")

    lines.append("## Explanation")
    lines.append("")
    lines.append("```text")
    lines.extend(explanation.splitlines())
    lines.append("```")
    lines.append("")

    if semantic_map:
        lines.append("## Parser Diagnostics")
        lines.append("")
        lines.append("```json")

        diagnostics = {
            name: {
                "parser_used": sem.parser_used,
                "parse_status": sem.parse_status,
                "parse_error": sem.parse_error,
            }
            for name, sem in semantic_map.items()
        }

        lines.append(json.dumps(diagnostics, indent=2))
        lines.append("```")
        lines.append("")

        lines.append("## Model Layers")
        lines.append("")
        lines.append("```json")

        layers = {name: sem.model_layer for name, sem in semantic_map.items()}

        lines.append(json.dumps(layers, indent=2))
        lines.append("```")
        lines.append("")

        lines.append("## Layer Summary")
        lines.append("")
        lines.append("```json")

        layer_summary = summarize_layers(semantic_map)

        lines.append(json.dumps(layer_summary, indent=2))
        lines.append("```")
        lines.append("")

        lines.append("## Model Complexity")
        lines.append("")
        lines.append("```json")

        complexity = {
            name: {
                "score": sem.complexity_score,
                "level": sem.complexity_level,
            }
            for name, sem in semantic_map.items()
        }

        lines.append(json.dumps(complexity, indent=2))
        lines.append("```")
        lines.append("")

    if summary["is_dag"]:
        structured_insights = summarize_insights(graph)
        insight_text = explain_insights(graph)

        lines.append("## Insights")
        lines.append("")
        lines.append("```text")
        lines.extend(insight_text.splitlines())
        lines.append("```")
        lines.append("")

        lines.append("## Structured Insights")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(structured_insights, indent=2))
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def write_markdown_report(
    graph: nx.DiGraph,
    output_path: str | Path = "output/pipeline_report.md",
    dag_image_path: str | Path | None = None,
    semantic_map: dict[str, SqlSemantics] | None = None,
) -> Path:
    """
    Write the Markdown pipeline report to disk.
    """
    output_file = ensure_parent_dir(output_path)
    report_text = generate_markdown_report(
        graph,
        dag_image_path=dag_image_path,
        semantic_map=semantic_map,
    )
    output_file.write_text(report_text, encoding="utf-8")
    return output_file


def write_graph_json(
    graph: nx.DiGraph,
    output_path: str | Path = "output/graph_data.json",
) -> Path:
    """
    Export graph structure to JSON.
    """
    output_file = ensure_parent_dir(output_path)
    data = export_graph_data(graph)
    output_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return output_file
