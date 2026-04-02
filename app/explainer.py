from __future__ import annotations

import networkx as nx


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


def explain_node(graph: nx.DiGraph, node: str) -> str:
    """
    Generate a plain-English explanation for a single node.
    """
    if node not in graph:
        raise ValueError(f"Node '{node}' does not exist in the graph.")

    attrs = graph.nodes[node]
    node_type = attrs.get("node_type", "unknown")
    upstream = get_upstream_nodes(graph, node)
    downstream = get_downstream_nodes(graph, node)

    if node_type == "source":
        if downstream:
            return f"{node} is a source table that feeds into {format_node_list(downstream)}."
        return f"{node} is a source table with no downstream models."

    if node_type == "final":
        if upstream:
            return f"{node} is a final output built from {format_node_list(upstream)}."
        return f"{node} is a final output with no identified upstream dependencies."

    if node_type == "intermediate":
        if upstream and downstream:
            return (
                f"{node} is an intermediate model built from "
                f"{format_node_list(upstream)} and used by "
                f"{format_node_list(downstream)}."
            )
        if upstream:
            return f"{node} is an intermediate model built from {format_node_list(upstream)}."
        if downstream:
            return (
                f"{node} is an intermediate model that feeds into {format_node_list(downstream)}."
            )
        return f"{node} is an intermediate model with isolated graph position."

    return (
        f"{node} is an unclassified node with upstream dependencies "
        f"{format_node_list(upstream)} and downstream dependents "
        f"{format_node_list(downstream)}."
    )


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


def explain_full_pipeline(graph: nx.DiGraph, max_paths: int = 5) -> str:
    """
    Generate a complete human-readable explanation of the pipeline.
    """
    sections = []

    sections.append("Pipeline Summary")
    sections.append(explain_pipeline_summary(graph))
    sections.append("")

    sections.append("Node Explanations")
    for node in sorted(graph.nodes()):
        sections.append(f"- {explain_node(graph, node)}")

    path_explanations = explain_lineage_paths(graph, max_paths=max_paths)
    if path_explanations:
        sections.append("")
        sections.append("Example Lineage Paths")
        for explanation in path_explanations:
            sections.append(f"- {explanation}")

    return "\n".join(sections)
