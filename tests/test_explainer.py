from app.explainer import (
    explain_full_pipeline,
    explain_lineage_paths,
    explain_node,
    explain_pipeline_summary,
)
from app.graph_builder import build_dag


def build_sample_graph():
    dependency_map = {
        "stg_orders": ["raw.orders"],
        "stg_customers": ["raw.customers"],
        "fct_sales": ["stg_orders", "stg_customers"],
    }
    return build_dag(dependency_map)


def test_explain_node_source():
    graph = build_sample_graph()
    text = explain_node(graph, "raw.orders")
    assert "source table" in text


def test_explain_node_final():
    graph = build_sample_graph()
    text = explain_node(graph, "fct_sales")
    assert "final output" in text
    assert "stg_orders" in text


def test_explain_pipeline_summary():
    graph = build_sample_graph()
    text = explain_pipeline_summary(graph)
    assert "5 nodes" in text
    assert "2 source nodes" in text
    assert "1 final outputs" in text


def test_explain_lineage_paths():
    graph = build_sample_graph()
    paths = explain_lineage_paths(graph, max_paths=5)
    assert len(paths) >= 1
    assert any("raw.orders -> stg_orders -> fct_sales" in path for path in paths)


def test_explain_full_pipeline():
    graph = build_sample_graph()
    text = explain_full_pipeline(graph)
    assert "Pipeline Summary" in text
    assert "Node Explanations" in text
    assert "Example Lineage Paths" in text
