from app.graph_builder import (
    build_dag,
    get_final_nodes,
    get_intermediate_nodes,
    get_source_nodes,
    graph_summary,
    is_dag,
)


def test_build_dag_basic():
    dependency_map = {
        "stg_orders": ["raw.orders"],
        "stg_customers": ["raw.customers"],
        "fct_sales": ["stg_orders", "stg_customers"],
    }

    graph = build_dag(dependency_map)

    assert graph.has_node("raw.orders")
    assert graph.has_node("stg_orders")
    assert graph.has_node("fct_sales")

    assert graph.has_edge("raw.orders", "stg_orders")
    assert graph.has_edge("stg_orders", "fct_sales")
    assert graph.has_edge("stg_customers", "fct_sales")


def test_node_classification():
    dependency_map = {
        "stg_orders": ["raw.orders"],
        "stg_customers": ["raw.customers"],
        "fct_sales": ["stg_orders", "stg_customers"],
    }

    graph = build_dag(dependency_map)

    assert "raw.orders" in get_source_nodes(graph)
    assert "raw.customers" in get_source_nodes(graph)

    assert "stg_orders" in get_intermediate_nodes(graph)
    assert "stg_customers" in get_intermediate_nodes(graph)

    assert "fct_sales" in get_final_nodes(graph)


def test_graph_is_dag():
    dependency_map = {
        "stg_orders": ["raw.orders"],
        "fct_sales": ["stg_orders"],
    }

    graph = build_dag(dependency_map)
    assert is_dag(graph) is True


def test_graph_summary():
    dependency_map = {
        "stg_orders": ["raw.orders"],
        "fct_sales": ["stg_orders"],
    }

    graph = build_dag(dependency_map)
    summary = graph_summary(graph)

    assert summary["num_nodes"] == 3
    assert summary["num_edges"] == 2
    assert summary["is_dag"] is True
    assert "raw.orders" in summary["sources"]
    assert "fct_sales" in summary["finals"]
