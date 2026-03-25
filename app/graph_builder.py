from __future__ import annotations

import networkx as nx

DependencyMap = dict[str, list[str]]


def build_dag(dependency_map: DependencyMap) -> nx.DiGraph:
    """
    Build a directed graph from a dependency map.

    Input format:
        {
            "fct_sales": ["stg_orders", "stg_customers"],
            "stg_orders": ["raw.orders"]
        }

    Edge direction:
        upstream -> downstream

    Example:
        stg_orders -> fct_sales
        raw.orders -> stg_orders
    """
    graph = nx.DiGraph()

    defined_models = set(dependency_map.keys())

    # Add model nodes first
    for model_name in defined_models:
        graph.add_node(
            model_name,
            label=model_name,
            defined_in_project=True,
            node_type="unknown",
        )

    # Add dependency edges
    for downstream_model, upstream_dependencies in dependency_map.items():
        for upstream in upstream_dependencies:
            if not graph.has_node(upstream):
                graph.add_node(
                    upstream,
                    label=upstream,
                    defined_in_project=False,
                    node_type="unknown",
                )

            graph.add_edge(upstream, downstream_model)

    # Classify nodes after edges are built
    classify_nodes(graph, defined_models)

    return graph


def classify_nodes(graph: nx.DiGraph, defined_models: set[str]) -> None:
    """
    Classify nodes as:
    - source: appears upstream only, not defined in project
    - final: defined in project and has no downstream dependents
    - intermediate: defined in project and participates in the middle
    """
    for node in graph.nodes:
        in_degree = graph.in_degree(node)
        out_degree = graph.out_degree(node)
        defined_in_project = node in defined_models

        if not defined_in_project:
            node_type = "source"
        elif out_degree == 0:
            node_type = "final"
        else:
            node_type = "intermediate"

        graph.nodes[node]["node_type"] = node_type
        graph.nodes[node]["in_degree"] = in_degree
        graph.nodes[node]["out_degree"] = out_degree


def is_dag(graph: nx.DiGraph) -> bool:
    """
    Return True if the graph is acyclic.
    """
    return nx.is_directed_acyclic_graph(graph)


def get_cycles(graph: nx.DiGraph) -> list[list[str]]:
    """
    Return a list of cycles if present.
    Empty list means the graph is acyclic.
    """
    try:
        cycles = list(nx.simple_cycles(graph))
        return cycles
    except nx.NetworkXNoCycle:
        return []


def get_source_nodes(graph: nx.DiGraph) -> list[str]:
    """
    Return nodes classified as sources.
    """
    return sorted(
        node for node, attrs in graph.nodes(data=True) if attrs.get("node_type") == "source"
    )


def get_final_nodes(graph: nx.DiGraph) -> list[str]:
    """
    Return nodes classified as final outputs.
    """
    return sorted(
        node for node, attrs in graph.nodes(data=True) if attrs.get("node_type") == "final"
    )


def get_intermediate_nodes(graph: nx.DiGraph) -> list[str]:
    """
    Return nodes classified as intermediate models.
    """
    return sorted(
        node for node, attrs in graph.nodes(data=True) if attrs.get("node_type") == "intermediate"
    )


def graph_summary(graph: nx.DiGraph) -> dict:
    """
    Return a lightweight summary of the graph for debugging and reporting.
    """
    return {
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "is_dag": is_dag(graph),
        "sources": get_source_nodes(graph),
        "intermediates": get_intermediate_nodes(graph),
        "finals": get_final_nodes(graph),
    }


def get_topological_order(graph: nx.DiGraph) -> list[str]:
    """
    Return topological order if graph is acyclic.
    Raise ValueError if cycles are present.
    """
    if not is_dag(graph):
        raise ValueError("Graph contains cycles; topological ordering is not possible.")

    return list(nx.topological_sort(graph))


def export_graph_data(graph: nx.DiGraph) -> dict:
    """
    Export graph into a JSON-friendly node/edge structure.
    """
    return {
        "nodes": [
            {
                "id": node,
                "label": attrs.get("label", node),
                "node_type": attrs.get("node_type", "unknown"),
                "defined_in_project": attrs.get("defined_in_project", False),
                "in_degree": attrs.get("in_degree", 0),
                "out_degree": attrs.get("out_degree", 0),
            }
            for node, attrs in graph.nodes(data=True)
        ],
        "edges": [{"source": source, "target": target} for source, target in graph.edges()],
    }
