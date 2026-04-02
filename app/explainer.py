from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx

if TYPE_CHECKING:
    from app.sql_intelligence import SqlSemantics


def format_node_list(nodes: list[str]) -> str:
    """
    Format a list of node names into readable English.
    """
    if not nodes:
        return "nothing"

    if len(nodes) == 1:
        return nodes[0]

    if len(nodes) == 2:
        return f"{nodes[0]} and {nodes[1]}"

    return f"{', '.join(nodes[:-1])}, and {nodes[-1]}"


def get_upstream_nodes(graph: nx.DiGraph, node: str) -> list[str]:
    """
    Return immediate upstream dependencies for a node.
    """
    return sorted(graph.predecessors(node))


def get_downstream_nodes(graph: nx.DiGraph, node: str) -> list[str]:
    """
    Return immediate downstream dependents for a node.
    """
    return sorted(graph.successors(node))


def _article(word: str | None) -> str:
    if not word:
        return "a"
    return "an" if word[0].lower() in "aeiou" else "a"


def _truncate(text: str, max_len: int = 80) -> str:
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def _cap_list(values: list[str], max_items: int = 3) -> str:
    if not values:
        return ""
    shown = values[:max_items]
    suffix = " ..." if len(values) > max_items else ""
    return ", ".join(shown) + suffix


def explain_sql_semantics(semantics: SqlSemantics) -> str:
    """
    Turn SQL semantic metadata into a readable sentence fragment.
    """
    parts: list[str] = []

    if semantics.dominant_pattern:
        article = _article(semantics.dominant_pattern)
        parts.append(f"is primarily {article} {semantics.dominant_pattern} model")

    if semantics.selected_columns:
        parts.append(f"selects {_cap_list(semantics.selected_columns, max_items=3)}")

    if semantics.table_aliases:
        alias_parts = [
            f"{alias}={table}" for alias, table in sorted(semantics.table_aliases.items())
        ]
        parts.append(f"uses aliases {_cap_list(alias_parts, max_items=3)}")

    if semantics.has_join:
        if semantics.join_types:
            join_text = "/".join(semantics.join_types)
            parts.append(f"uses {join_text} join logic")
        else:
            parts.append("uses join logic")

        if semantics.join_keys:
            parts.append(f"joins on {_cap_list(semantics.join_keys, max_items=2)}")
        elif semantics.join_conditions:
            parts.append(f"uses join conditions like {_truncate(semantics.join_conditions[0])}")

    if semantics.has_group_by:
        if semantics.group_by_columns:
            parts.append(f"aggregates by {_cap_list(semantics.group_by_columns, max_items=3)}")
        else:
            parts.append("performs aggregation")

    if semantics.aggregate_functions:
        parts.append(
            f"uses aggregate functions: {_cap_list(semantics.aggregate_functions, max_items=4)}"
        )

    if semantics.has_where and semantics.where_clause:
        parts.append(f"filters rows using {_truncate(semantics.where_clause)}")

    if semantics.has_having and semantics.having_clause:
        parts.append(f"applies having logic using {_truncate(semantics.having_clause)}")

    if semantics.has_distinct:
        parts.append("uses distinct selection")

    if semantics.has_window_functions:
        if semantics.window_functions:
            parts.append(
                f"uses window functions: {_cap_list(semantics.window_functions, max_items=4)}"
            )
        else:
            parts.append("uses window functions")

    if semantics.has_union:
        parts.append("combines datasets with union")

    if semantics.cte_count > 0:
        parts.append(f"contains {semantics.cte_count} CTE(s)")

    if semantics.has_subquery:
        parts.append("includes subqueries")

    if not parts:
        return "appears to be a relatively simple transformation"

    return ", ".join(parts)


def explain_node(
    graph: nx.DiGraph,
    node: str,
    semantic_map: dict[str, SqlSemantics] | None = None,
) -> str:
    """
    Generate a plain-English explanation for a single node.
    """
    if node not in graph:
        raise ValueError(f"Node '{node}' does not exist in the graph.")

    attrs = graph.nodes[node]
    node_type = attrs.get("node_type", "unknown")
    upstream = get_upstream_nodes(graph, node)
    downstream = get_downstream_nodes(graph, node)

    base_text: str

    if node_type == "source":
        if downstream:
            base_text = f"{node} is a source table that feeds into {format_node_list(downstream)}."
        else:
            base_text = f"{node} is a source table with no downstream models."
    elif node_type == "final":
        if upstream:
            base_text = f"{node} is a final output built from {format_node_list(upstream)}."
        else:
            base_text = f"{node} is a final output with no identified upstream dependencies."
    elif node_type == "intermediate":
        if upstream and downstream:
            base_text = (
                f"{node} is an intermediate model built from "
                f"{format_node_list(upstream)} and used by "
                f"{format_node_list(downstream)}."
            )
        elif upstream:
            base_text = f"{node} is an intermediate model built from {format_node_list(upstream)}."
        elif downstream:
            base_text = (
                f"{node} is an intermediate model that feeds into {format_node_list(downstream)}."
            )
        else:
            base_text = f"{node} is an intermediate model with isolated graph position."
    else:
        base_text = (
            f"{node} is an unclassified node with upstream dependencies "
            f"{format_node_list(upstream)} and downstream dependents "
            f"{format_node_list(downstream)}."
        )

    if semantic_map and node in semantic_map:
        semantic_text = explain_sql_semantics(semantic_map[node])
        return f"{base_text} It {semantic_text}."

    return base_text


def explain_pipeline_summary(graph: nx.DiGraph) -> str:
    """
    Generate a summary of the full pipeline.
    """
    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()

    sources = sorted(
        node for node, attrs in graph.nodes(data=True) if attrs.get("node_type") == "source"
    )
    intermediates = sorted(
        node for node, attrs in graph.nodes(data=True) if attrs.get("node_type") == "intermediate"
    )
    finals = sorted(
        node for node, attrs in graph.nodes(data=True) if attrs.get("node_type") == "final"
    )

    return (
        f"This pipeline contains {num_nodes} nodes and {num_edges} dependency edges. "
        f"It starts from {len(sources)} source nodes: {format_node_list(sources)}. "
        f"It includes {len(intermediates)} intermediate models: "
        f"{format_node_list(intermediates)}. "
        f"It produces {len(finals)} final outputs: {format_node_list(finals)}."
    )


def get_lineage_paths(graph: nx.DiGraph, max_paths: int = 10) -> list[list[str]]:
    """
    Return source-to-final lineage paths.
    """
    sources = [node for node, attrs in graph.nodes(data=True) if attrs.get("node_type") == "source"]
    finals = [node for node, attrs in graph.nodes(data=True) if attrs.get("node_type") == "final"]

    all_paths: list[list[str]] = []

    for source in sorted(sources):
        for final in sorted(finals):
            if nx.has_path(graph, source, final):
                paths = list(nx.all_simple_paths(graph, source=source, target=final))
                for path in paths:
                    all_paths.append(path)
                    if len(all_paths) >= max_paths:
                        return all_paths

    return all_paths


def explain_lineage_paths(graph: nx.DiGraph, max_paths: int = 5) -> list[str]:
    """
    Generate readable explanations for source-to-final paths.
    """
    paths = get_lineage_paths(graph, max_paths=max_paths)

    explanations = []
    for path in paths:
        explanations.append(f"Lineage path: {' -> '.join(path)}")

    return explanations


def explain_full_pipeline(
    graph: nx.DiGraph,
    semantic_map: dict[str, SqlSemantics] | None = None,
    max_paths: int = 5,
) -> str:
    """
    Generate a complete human-readable explanation of the pipeline.
    """
    sections: list[str] = []

    sections.append("Pipeline Summary")
    sections.append(explain_pipeline_summary(graph))
    sections.append("")

    sections.append("Node Explanations")
    for node in sorted(graph.nodes()):
        sections.append(f"- {explain_node(graph, node, semantic_map=semantic_map)}")

    path_explanations = explain_lineage_paths(graph, max_paths=max_paths)
    if path_explanations:
        sections.append("")
        sections.append("Example Lineage Paths")
        for explanation in path_explanations:
            sections.append(f"- {explanation}")

    return "\n".join(sections)
