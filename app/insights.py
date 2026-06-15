from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.sql_intelligence import SqlSemantics
import networkx as nx


def get_pipeline_depth(graph: nx.DiGraph) -> int:
    """
    Return the length of the longest path in the DAG, measured in edges.
    """
    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError("Pipeline depth can only be computed for a DAG.")

    if graph.number_of_nodes() == 0:
        return 0

    return nx.dag_longest_path_length(graph)


def get_longest_path(graph: nx.DiGraph) -> list[str]:
    """
    Return one of the longest lineage paths in the DAG.
    """
    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError("Longest path can only be computed for a DAG.")

    if graph.number_of_nodes() == 0:
        return []

    return list(nx.dag_longest_path(graph))


def get_high_fan_in_nodes(graph: nx.DiGraph, min_fan_in: int = 2) -> list[dict[str, Any]]:
    """
    Return nodes with multiple upstream dependencies.
    """
    results: list[dict[str, Any]] = []

    for node in graph.nodes:
        fan_in = graph.in_degree(node)
        if fan_in >= min_fan_in:
            results.append(
                {
                    "node": node,
                    "fan_in": fan_in,
                    "upstreams": sorted(graph.predecessors(node)),
                    "node_type": graph.nodes[node].get("node_type", "unknown"),
                }
            )

    results.sort(key=lambda item: (-item["fan_in"], item["node"]))
    return results


def get_high_fan_out_nodes(graph: nx.DiGraph, min_fan_out: int = 2) -> list[dict[str, Any]]:
    """
    Return nodes used by multiple downstream models.
    """
    results: list[dict[str, Any]] = []

    for node in graph.nodes:
        fan_out = graph.out_degree(node)
        if fan_out >= min_fan_out:
            results.append(
                {
                    "node": node,
                    "fan_out": fan_out,
                    "downstreams": sorted(graph.successors(node)),
                    "node_type": graph.nodes[node].get("node_type", "unknown"),
                }
            )

    results.sort(key=lambda item: (-item["fan_out"], item["node"]))
    return results


def get_isolated_nodes(graph: nx.DiGraph) -> list[str]:
    """
    Return nodes with no incoming or outgoing edges.
    """
    return sorted(node for node in graph.nodes if graph.degree(node) == 0)


def get_node_depths(graph: nx.DiGraph) -> dict[str, int]:
    """
    Compute depth of each node as the longest distance from any source node.
    Sources have depth 0.
    """
    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError("Node depths can only be computed for a DAG.")

    depths: dict[str, int] = {}

    for node in nx.topological_sort(graph):
        predecessors = list(graph.predecessors(node))
        if not predecessors:
            depths[node] = 0
        else:
            depths[node] = max(depths[pred] for pred in predecessors) + 1

    return depths


def get_deepest_nodes(graph: nx.DiGraph, top_n: int = 5) -> list[dict[str, Any]]:
    """
    Return nodes that are deepest in the pipeline.
    """
    depths = get_node_depths(graph)

    results = [
        {
            "node": node,
            "depth": depth,
            "node_type": graph.nodes[node].get("node_type", "unknown"),
        }
        for node, depth in depths.items()
    ]

    results.sort(key=lambda item: (-item["depth"], item["node"]))
    return results[:top_n]


def summarize_insights(graph: nx.DiGraph) -> dict[str, Any]:
    """
    Return a structured summary of pipeline insights.
    """
    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError("Insights summary requires a DAG.")

    return {
        "pipeline_depth": get_pipeline_depth(graph),
        "longest_path": get_longest_path(graph),
        "high_fan_in_nodes": get_high_fan_in_nodes(graph),
        "high_fan_out_nodes": get_high_fan_out_nodes(graph),
        "isolated_nodes": get_isolated_nodes(graph),
        "deepest_nodes": get_deepest_nodes(graph),
    }


def explain_insights(graph: nx.DiGraph) -> str:
    """
    Generate plain-English insight statements from graph structure.
    """
    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError("Insight explanations require a DAG.")

    lines: list[str] = []

    depth = get_pipeline_depth(graph)
    longest_path = get_longest_path(graph)
    fan_in_nodes = get_high_fan_in_nodes(graph)
    fan_out_nodes = get_high_fan_out_nodes(graph)
    isolated_nodes = get_isolated_nodes(graph)
    deepest_nodes = get_deepest_nodes(graph)

    lines.append("Pipeline Insights")
    lines.append(f"- The pipeline depth is {depth} step(s).")

    if longest_path:
        lines.append(f"- One of the longest lineage paths is: {' -> '.join(longest_path)}.")

    if fan_in_nodes:
        for item in fan_in_nodes[:3]:
            lines.append(
                f"- {item['node']} has {item['fan_in']} upstream dependencies, "
                f"which makes it a relatively complex transformation node."
            )
    else:
        lines.append("- No nodes have high fan-in in the current pipeline.")

    if fan_out_nodes:
        for item in fan_out_nodes[:3]:
            lines.append(
                f"- {item['node']} feeds {item['fan_out']} downstream models, "
                f"making it a central dependency in the pipeline."
            )
    else:
        lines.append("- No nodes have high fan-out in the current pipeline.")

    if deepest_nodes:
        top = deepest_nodes[0]
        lines.append(f"- The deepest node is {top['node']} at depth {top['depth']}.")

    if isolated_nodes:
        lines.append(f"- Isolated nodes detected: {', '.join(isolated_nodes)}.")

    return "\n".join(lines)


def compute_model_complexity(semantics: SqlSemantics) -> tuple[int, str]:
    score = 0

    # joins
    score += semantics.join_count * 2

    # dependencies
    score += len(semantics.source_tables)

    # aggregation
    if semantics.has_group_by:
        score += 2

    # window functions
    if semantics.has_window_functions:
        score += 3

    # subqueries
    if semantics.has_subquery:
        score += 2

    # CTEs
    score += semantics.cte_count

    # union
    if semantics.has_union:
        score += 2

    # classify
    if score <= 2:
        level = "low"
    elif score <= 6:
        level = "medium"
    else:
        level = "high"

    return score, level
