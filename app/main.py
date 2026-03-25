from __future__ import annotations

import json
import sys
from pathlib import Path

from app.graph_builder import build_dag, get_topological_order, graph_summary
from app.parser import parse_sql_folder


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m app.main <sql_folder>")
        sys.exit(1)

    folder = Path(sys.argv[1])

    dependency_map = parse_sql_folder(folder)
    graph = build_dag(dependency_map)

    print("=== Dependency Map ===")
    print(json.dumps(dependency_map, indent=2))

    print("\n=== Graph Summary ===")
    print(json.dumps(graph_summary(graph), indent=2))

    if graph_summary(graph)["is_dag"]:
        print("\n=== Topological Order ===")
        print(json.dumps(get_topological_order(graph), indent=2))


if __name__ == "__main__":
    main()
