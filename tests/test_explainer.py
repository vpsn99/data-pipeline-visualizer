from app.explainer import (
    explain_full_pipeline,
    explain_lineage_paths,
    explain_node,
    explain_pipeline_summary,
)
from app.graph_builder import build_dag
from app.sql_intelligence import analyze_sql


def test_explain_node_with_semantics():
    graph = build_sample_graph()

    sql = """
    select
        c.customer_name,
        sum(o.amount) as total_amount
    from stg_orders o
    inner join stg_customers c
        on o.customer_id = c.customer_id
    group by c.customer_name
    """
    semantic_map = {
        "fct_sales": analyze_sql("fct_sales", sql),
    }

    text = explain_node(graph, "fct_sales", semantic_map=semantic_map)
    assert "join" in text.lower()
    assert "aggregation" in text.lower()


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


def test_explain_node_with_richer_semantics():
    graph = build_sample_graph()

    sql = """
    select
        c.customer_name,
        sum(o.amount) as total_amount
    from stg_orders o
    inner join stg_customers c
        on o.customer_id = c.customer_id
    where o.amount > 0
    group by c.customer_name
    """
    semantic_map = {
        "fct_sales": analyze_sql("fct_sales", sql),
    }

    text = explain_node(graph, "fct_sales", semantic_map=semantic_map)
    assert "aggregation model" in text or "primarily a aggregation model" in text
    assert "joins on" in text
    assert "filters rows" in text


def test_explain_node_with_phase3_semantics():
    graph = build_sample_graph()

    sql = """
    select
        c.customer_name,
        sum(o.amount) as total_amount,
        count(*) as order_count
    from stg_orders o
    inner join stg_customers c
        on o.customer_id = c.customer_id
    where o.amount > 0
    group by c.customer_name
    """
    semantic_map = {
        "fct_sales": analyze_sql("fct_sales", sql),
    }

    text = explain_node(graph, "fct_sales", semantic_map=semantic_map)

    assert "selects" in text.lower()
    assert "aliases" in text.lower()
    assert "joins on" in text.lower()
    assert "aggregate" in text.lower()
