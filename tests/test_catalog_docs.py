from app.catalog_docs import generate_catalog_docs, generate_model_doc, safe_filename


def test_safe_filename():
    assert safe_filename("fct_sales") == "fct_sales.md"
    assert safe_filename("raw.orders") == "raw.orders.md"


def test_generate_model_doc():
    metadata = {
        "node_type": "final",
        "layer": "fact",
        "complexity_level": "medium",
        "complexity_score": 6,
        "dominant_pattern": "aggregation",
        "dependencies": ["int_customer_orders"],
        "downstream_models": [],
        "join_count": 0,
        "join_types": [],
        "join_keys": [],
        "aggregate_functions": ["sum", "count"],
        "group_by_columns": ["customer_name"],
        "where_clause": None,
        "selected_columns": ["customer_name", "sum(amount) as total_amount"],
        "parser_used": "sqlglot",
        "parse_status": "success",
        "parse_error": None,
    }

    doc = generate_model_doc("fct_sales", metadata)

    assert "# fct_sales" in doc
    assert "**Layer:** fact" in doc
    assert "int_customer_orders" in doc
    assert "sum" in doc
    assert "**Parser Used:** sqlglot" in doc


def test_generate_catalog_docs(tmp_path):
    catalog = {
        "fct_sales": {
            "node_type": "final",
            "layer": "fact",
            "complexity_level": "medium",
            "complexity_score": 6,
            "dominant_pattern": "aggregation",
            "dependencies": ["stg_orders"],
            "downstream_models": [],
            "join_count": 0,
            "join_types": [],
            "join_keys": [],
            "aggregate_functions": ["sum"],
            "group_by_columns": ["customer_id"],
            "where_clause": None,
            "selected_columns": [],
            "parser_used": "sqlglot",
            "parse_status": "success",
            "parse_error": None,
        }
    }

    written_files = generate_catalog_docs(catalog, output_dir=tmp_path)

    assert len(written_files) == 1
    assert written_files[0].exists()
    assert written_files[0].name == "fct_sales.md"
