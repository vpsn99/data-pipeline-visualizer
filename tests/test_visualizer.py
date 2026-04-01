from pathlib import Path

from app.graph_builder import build_dag
from app.visualizer import render_dag


def test_render_dag_networkx(tmp_path: Path):
    dependency_map = {
        "stg_orders": ["raw.orders"],
        "stg_customers": ["raw.customers"],
        "fct_sales": ["stg_orders", "stg_customers"],
    }

    graph = build_dag(dependency_map)
    output_file = tmp_path / "pipeline_dag.png"

    rendered_file = render_dag(graph, output_file, engine="networkx")

    assert rendered_file.exists()
    assert rendered_file.suffix == ".png"
