from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.explainer import explain_full_pipeline
from app.graph_builder import build_dag, get_topological_order, graph_summary
from app.insights import explain_insights, summarize_insights
from app.model_catalog import write_model_catalog
from app.parser import parse_sql_folder
from app.reporter import write_graph_json, write_markdown_report
from app.sql_intelligence import analyze_sql_folder
from app.visualizer import render_dag


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Visualize and analyze SQL/dbt-style data pipelines."
    )
    parser.add_argument(
        "sql_folder",
        help="Path to folder containing SQL model files.",
    )
    parser.add_argument(
        "--parser",
        choices=["heuristic", "sqlglot", "auto"],
        default="auto",
        help="SQL parsing backend to use.",
    )
    parser.add_argument(
        "--dialect",
        default=None,
        help="Optional SQL dialect for sqlglot, e.g. snowflake, spark, duckdb.",
    )
    parser.add_argument(
        "--no-visual",
        action="store_true",
        help="Skip DAG image generation.",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate report and JSON output without printing long explanations.",
    )
    return parser


def resolve_sqlglot_usage(parser_mode: str) -> bool:
    """
    Decide whether sqlglot should be used.
    For now:
    - heuristic -> False
    - sqlglot -> True
    - auto -> True
    """
    return parser_mode in {"sqlglot", "auto"}


def main() -> None:
    arg_parser = build_arg_parser()
    args = arg_parser.parse_args()

    folder = Path(args.sql_folder)
    use_sqlglot = resolve_sqlglot_usage(args.parser)

    dependency_map = parse_sql_folder(folder)
    semantic_map = analyze_sql_folder(
        folder,
        use_sqlglot=use_sqlglot,
        dialect=args.dialect,
    )

    graph = build_dag(dependency_map)
    summary = graph_summary(graph)

    print("=== SQL Parser Mode ===")
    if use_sqlglot:
        dialect_text = args.dialect if args.dialect else "default"
        print(f"{args.parser} (sqlglot enabled, dialect={dialect_text})")
    else:
        print("heuristic only")

    print("\n=== Dependency Map ===")
    print(json.dumps(dependency_map, indent=2))

    print("\n=== SQL Intelligence ===")
    print(
        json.dumps(
            {name: semantics.to_dict() for name, semantics in semantic_map.items()},
            indent=2,
        )
    )

    print("\n=== Parser Diagnostics ===")

    diagnostics = {
        name: {
            "parser_used": sem.parser_used,
            "parse_status": sem.parse_status,
            "parse_error": sem.parse_error,
        }
        for name, sem in semantic_map.items()
    }

    print(json.dumps(diagnostics, indent=2))

    print("\n=== Graph Summary ===")
    print(json.dumps(summary, indent=2))

    dag_image_file: Path | None = None

    if summary["is_dag"]:
        print("\n=== Topological Order ===")
        print(json.dumps(get_topological_order(graph), indent=2))

        if not args.no_visual:
            dag_image_file = render_dag(
                graph,
                "output/pipeline_dag.png",
                engine="auto",
            )
            print("\n=== DAG Image Saved ===")
            print(dag_image_file)

        if not args.report_only:
            print("\n=== Pipeline Explanation ===")
            print(explain_full_pipeline(graph, semantic_map=semantic_map))

            print("\n=== Structured Insights ===")
            print(json.dumps(summarize_insights(graph), indent=2))

            print("\n=== Insight Narration ===")
            print(explain_insights(graph))

        report_file = write_markdown_report(
            graph,
            output_path="output/pipeline_report.md",
            dag_image_path=dag_image_file,
            semantic_map=semantic_map,
        )
        print("\n=== Markdown Report Saved ===")
        print(report_file)

        graph_json_file = write_graph_json(
            graph,
            output_path="output/graph_data.json",
        )
        print("\n=== Graph JSON Saved ===")
        print(graph_json_file)

        model_catalog_file = write_model_catalog(
            graph,
            semantic_map,
            output_path="output/model_catalog.json",
        )
        print("\n=== Model Catalog Saved ===")
        print(model_catalog_file)

    else:
        print("\nGraph contains cycles, so DAG visualization may not be reliable.")


if __name__ == "__main__":
    main()
