from pathlib import Path

from app.graph_builder import build_dag
from app.reporter import generate_markdown_report, write_graph_json, write_markdown_report


def build_sample_graph():
    dependency_map = {
        "stg_orders": ["raw.orders"],
        "stg_customers": ["raw.customers"],
        "fct_sales": ["stg_orders", "stg_customers"],
    }
    return build_dag(dependency_map)


def test_generate_markdown_report():
    graph = build_sample_graph()
    report = generate_markdown_report(graph, dag_image_path="output/pipeline_dag.png")

    assert "# Data Pipeline Report" in report
    assert "## Graph Summary" in report
    assert "## Explanation" in report
    assert "## Insights" in report


def test_write_markdown_report(tmp_path: Path):
    graph = build_sample_graph()
    output_file = tmp_path / "pipeline_report.md"

    written_file = write_markdown_report(
        graph,
        output_path=output_file,
        dag_image_path="output/pipeline_dag.png",
    )

    assert written_file.exists()
    assert written_file.suffix == ".md"


def test_write_graph_json(tmp_path: Path):
    graph = build_sample_graph()
    output_file = tmp_path / "graph_data.json"

    written_file = write_graph_json(graph, output_path=output_file)

    assert written_file.exists()
    assert written_file.suffix == ".json"
