from app.graph_builder import build_dag
from app.insights import (
    explain_insights,
    get_deepest_nodes,
    get_high_fan_in_nodes,
    get_high_fan_out_nodes,
    get_longest_path,
    get_pipeline_depth,
    summarize_insights,
)


def build_sample_graph():
    dependency_map = {
        "stg_orders": ["raw.orders"],
        "stg_customers": ["raw.customers"],
        "fct_sales": ["stg_orders", "stg_customers"],
    }
    return build_dag(dependency_map)


def test_pipeline_depth():
    graph = build_sample_graph()
    assert get_pipeline_depth(graph) == 2


def test_longest_path():
    graph = build_sample_graph()
    path = get_longest_path(graph)
    assert len(path) == 3
    assert path[-1] == "fct_sales"


def test_high_fan_in_nodes():
    graph = build_sample_graph()
    results = get_high_fan_in_nodes(graph)
    assert any(item["node"] == "fct_sales" and item["fan_in"] == 2 for item in results)


def test_high_fan_out_nodes():
    dependency_map = {
        "stg_orders": ["raw.orders"],
        "fct_sales": ["stg_orders"],
        "agg_sales": ["stg_orders"],
    }
    graph = build_dag(dependency_map)
    results = get_high_fan_out_nodes(graph)
    assert any(item["node"] == "stg_orders" and item["fan_out"] == 2 for item in results)


def test_deepest_nodes():
    graph = build_sample_graph()
    results = get_deepest_nodes(graph)
    assert results[0]["node"] == "fct_sales"
    assert results[0]["depth"] == 2


def test_summarize_insights():
    graph = build_sample_graph()
    summary = summarize_insights(graph)
    assert summary["pipeline_depth"] == 2
    assert "longest_path" in summary
    assert "high_fan_in_nodes" in summary


def test_explain_insights():
    graph = build_sample_graph()
    text = explain_insights(graph)
    assert "Pipeline Insights" in text
    assert "pipeline depth" in text.lower()
    assert "fct_sales" in text
