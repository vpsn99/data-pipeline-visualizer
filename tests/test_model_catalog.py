from pathlib import Path

from app.graph_builder import build_dag
from app.model_catalog import build_model_catalog, write_model_catalog
from app.sql_intelligence import analyze_sql


def test_build_model_catalog():
    dependency_map = {
        "stg_orders": ["raw.orders"],
        "fct_sales": ["stg_orders"],
    }
    graph = build_dag(dependency_map)

    semantic_map = {
        "stg_orders": analyze_sql("stg_orders", "select * from raw.orders"),
        "fct_sales": analyze_sql(
            "fct_sales",
            """
            select
                customer_id,
                sum(amount) as total_amount
            from stg_orders
            group by customer_id
            """,
        ),
    }

    catalog = build_model_catalog(graph, semantic_map)

    assert "fct_sales" in catalog
    assert catalog["fct_sales"]["layer"] == "fact"
    assert catalog["fct_sales"]["dependencies"] == ["stg_orders"]
    assert catalog["fct_sales"]["dominant_pattern"] == "aggregation"
    assert catalog["raw.orders"]["node_type"] == "source"


def test_write_model_catalog(tmp_path: Path):
    dependency_map = {
        "stg_orders": ["raw.orders"],
        "fct_sales": ["stg_orders"],
    }
    graph = build_dag(dependency_map)

    semantic_map = {
        "stg_orders": analyze_sql("stg_orders", "select * from raw.orders"),
        "fct_sales": analyze_sql("fct_sales", "select * from stg_orders"),
    }

    output_file = tmp_path / "model_catalog.json"

    written_file = write_model_catalog(
        graph,
        semantic_map,
        output_path=output_file,
    )

    assert written_file.exists()
    assert written_file.suffix == ".json"
