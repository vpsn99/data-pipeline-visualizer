from __future__ import annotations

import json
import sys
from pathlib import Path

from app.explainer import explain_full_pipeline
from app.graph_builder import build_dag, get_topological_order, graph_summary
from app.insights import explain_insights, summarize_insights
from app.parser import parse_sql_folder
from app.visualizer import render_dag


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m app.main <sql_folder>")
        sys.exit(1)

    folder = Path(sys.argv[1])

    dependency_map = parse_sql_folder(folder)
    graph = build_dag(dependency_map)
    summary = graph_summary(graph)

    print("=== Dependency Map ===")
    print(json.dumps(dependency_map, indent=2))

    print("\n=== Graph Summary ===")
    print(json.dumps(summary, indent=2))

    if summary["is_dag"]:
        print("\n=== Topological Order ===")
        print(json.dumps(get_topological_order(graph), indent=2))

        output_file = render_dag(graph, "output/pipeline_dag.png", engine="auto")
        print("\n=== DAG Image Saved ===")
        print(output_file)

        print("\n=== Pipeline Explanation ===")
        print(explain_full_pipeline(graph))

        print("\n=== Structured Insights ===")
        print(json.dumps(summarize_insights(graph), indent=2))

        print("\n=== Insight Narration ===")
        print(explain_insights(graph))
    else:
        print("\nGraph contains cycles, so DAG visualization may not be reliable.")


if __name__ == "__main__":
    main()
