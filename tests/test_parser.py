from app.parser import extract_dependencies


def test_extract_ref_dependencies():
    sql = """
    select *
    from {{ ref('stg_orders') }} o
    join {{ ref("stg_customers") }} c
      on o.customer_id = c.customer_id
    """
    deps = extract_dependencies(sql)
    assert "stg_orders" in deps
    assert "stg_customers" in deps


def test_extract_raw_table_dependencies():
    sql = """
    select *
    from raw.orders o
    join analytics.customers c
      on o.customer_id = c.customer_id
    """
    deps = extract_dependencies(sql)
    assert "raw.orders" in deps
    assert "analytics.customers" in deps
