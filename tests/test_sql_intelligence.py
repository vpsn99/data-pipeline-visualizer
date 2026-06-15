from app.sql_intelligence import analyze_sql


def test_detect_join_group_filter():
    sql = """
    select
        c.customer_name,
        sum(o.amount) as total_amount
    from orders o
    inner join customers c
        on o.customer_id = c.customer_id
    where o.amount > 0
    group by c.customer_name
    """
    semantics = analyze_sql("customer_sales", sql)

    assert semantics.has_join is True
    assert semantics.join_count >= 1
    assert "inner" in semantics.join_types
    assert semantics.has_where is True
    assert semantics.has_group_by is True
    assert "aggregation" in semantics.inferred_patterns
    assert "join_enrichment" in semantics.inferred_patterns
    assert "filtering" in semantics.inferred_patterns


def test_detect_distinct_and_order_by():
    sql = """
    select distinct customer_id
    from orders
    order by customer_id
    """
    semantics = analyze_sql("distinct_customers", sql)

    assert semantics.has_distinct is True
    assert semantics.has_order_by is True


def test_detect_cte_and_window_function():
    sql = """
    with ranked_orders as (
        select
            order_id,
            customer_id,
            row_number() over (partition by customer_id order by order_id desc) as rn
        from orders
    )
    select *
    from ranked_orders
    where rn = 1
    """
    semantics = analyze_sql("latest_orders", sql)

    assert semantics.cte_count >= 1
    assert semantics.has_window_functions is True
    assert semantics.has_where is True


def test_detect_union():
    sql = """
    select customer_id from us_customers
    union all
    select customer_id from eu_customers
    """
    semantics = analyze_sql("all_customers", sql)

    assert semantics.has_union is True
    assert "union_combination" in semantics.inferred_patterns


def test_extract_group_by_columns_and_aggregates():
    sql = """
    select
        customer_name,
        sum(amount) as total_amount,
        count(*) as order_count
    from orders
    group by customer_name
    """
    semantics = analyze_sql("customer_sales", sql)

    assert semantics.has_group_by is True
    assert "customer_name" in semantics.group_by_columns
    assert "sum" in semantics.aggregate_functions
    assert "count" in semantics.aggregate_functions
    assert semantics.dominant_pattern == "aggregation"


def test_extract_where_and_having_clause():
    sql = """
    select
        customer_id,
        sum(amount) as total_amount
    from orders
    where amount > 0
    group by customer_id
    having sum(amount) > 100
    """
    semantics = analyze_sql("qualified_customers", sql)

    assert semantics.where_clause == "amount > 0"
    assert semantics.having_clause == "sum(amount) > 100"
    assert semantics.has_having is True


def test_extract_join_conditions():
    sql = """
    select *
    from orders o
    left join customers c
        on o.customer_id = c.customer_id
    """
    semantics = analyze_sql("orders_with_customers", sql)

    assert semantics.has_join is True
    assert "left" in semantics.join_types
    assert len(semantics.join_conditions) >= 1
    assert "o.customer_id = c.customer_id" in semantics.join_conditions[0]


def test_extract_selected_columns():
    sql = """
    select
        c.customer_name,
        sum(o.amount) as total_amount,
        count(*) as order_count
    from orders o
    """
    semantics = analyze_sql("customer_sales", sql)

    assert len(semantics.selected_columns) == 3
    assert "c.customer_name" in semantics.selected_columns
    assert "sum(o.amount) as total_amount" in semantics.selected_columns


def test_extract_table_aliases():
    sql = """
    select *
    from orders o
    inner join customers as c
        on o.customer_id = c.customer_id
    """
    semantics = analyze_sql("orders_with_customers", sql)

    assert semantics.table_aliases["o"] == "orders"
    assert semantics.table_aliases["c"] == "customers"


def test_extract_join_keys():
    sql = """
    select *
    from orders o
    left join customers c
        on o.customer_id = c.customer_id
       and o.region_id = c.region_id
    """
    semantics = analyze_sql("orders_with_customers", sql)

    assert "o.customer_id = c.customer_id" in semantics.join_keys
    assert "o.region_id = c.region_id" in semantics.join_keys


def test_extract_window_function_names():
    sql = """
    select
        customer_id,
        row_number() over (partition by customer_id order by created_at desc) as rn,
        lag(amount) over (partition by customer_id order by created_at) as prev_amount
    from orders
    """
    semantics = analyze_sql("ranked_orders", sql)

    assert semantics.has_window_functions is True
    assert "row_number" in semantics.window_functions
    assert "lag" in semantics.window_functions


def test_parser_fallback_behavior():
    # deliberately malformed SQL
    sql = "select from where broken syntax"

    semantics = analyze_sql(
        model_name="bad_model",
        sql=sql,
        use_sqlglot=True,
    )

    assert semantics.parser_used in {"heuristic", "sqlglot"}
    assert semantics.parse_status in {"success", "fallback"}


def test_complexity_scoring():
    sql = """
    select
        c.customer_name,
        sum(o.amount)
    from orders o
    join customers c on o.customer_id = c.customer_id
    group by c.customer_name
    """

    semantics = analyze_sql("test_model", sql)

    assert semantics.complexity_score > 0
    assert semantics.complexity_level in {"low", "medium", "high"}
