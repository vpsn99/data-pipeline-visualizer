from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import networkx as nx

if TYPE_CHECKING:
    from app.sql_intelligence import SqlSemantics


def build_model_catalog(
    graph: nx.DiGraph,
    semantic_map: dict[str, SqlSemantics],
) -> dict[str, dict[str, Any]]:
    """
    Build a model-level catalog combining graph lineage and SQL semantics.
    """
    catalog: dict[str, dict[str, Any]] = {}

    for node in sorted(graph.nodes()):
        semantics = semantic_map.get(node)

        catalog[node] = {
            "node_type": graph.nodes[node].get("node_type", "unknown"),
            "layer": getattr(
                semantics, "model_layer", "source" if graph.in_degree(node) == 0 else "other"
            ),
            "dependencies": sorted(graph.predecessors(node)),
            "downstream_models": sorted(graph.successors(node)),
            "in_degree": graph.in_degree(node),
            "out_degree": graph.out_degree(node),
            "complexity_score": getattr(semantics, "complexity_score", 0),
            "complexity_level": getattr(semantics, "complexity_level", "low"),
            "dominant_pattern": getattr(semantics, "dominant_pattern", None),
            "parser_used": getattr(semantics, "parser_used", None),
            "parse_status": getattr(semantics, "parse_status", None),
            "parse_error": getattr(semantics, "parse_error", None),
            "source_tables": getattr(semantics, "source_tables", []),
            "join_count": getattr(semantics, "join_count", 0),
            "join_types": getattr(semantics, "join_types", []),
            "join_keys": getattr(semantics, "join_keys", []),
            "group_by_columns": getattr(semantics, "group_by_columns", []),
            "aggregate_functions": getattr(semantics, "aggregate_functions", []),
            "where_clause": getattr(semantics, "where_clause", None),
            "selected_columns": getattr(semantics, "selected_columns", []),
        }

    return catalog


def write_model_catalog(
    graph: nx.DiGraph,
    semantic_map: dict[str, SqlSemantics],
    output_path: str | Path = "output/model_catalog.json",
) -> Path:
    """
    Write model catalog JSON to disk.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    catalog = build_model_catalog(graph, semantic_map)
    output_file.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

    return output_file
