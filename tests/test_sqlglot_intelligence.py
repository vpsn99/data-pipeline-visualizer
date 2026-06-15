from app.sqlglot_intelligence import analyze_with_sqlglot


def test_sqlglot_extracts_selected_columns_and_group_by():
    sql = """
    select
        c.customer_name,
        sum(o.amount) as total_amount,
        count(*) as order_count
    from orders o
    inner join customers c
        on o.customer_id = c.customer_id
    where o.amount > 0
    group by c.customer_name
    having sum(o.amount) > 100
    """

    result = analyze_with_sqlglot(sql)

    assert result.parse_error is None
    assert "c.customer_name" in result.selected_columns
    assert "sum(o.amount) AS total_amount" in result.selected_columns or any(
        "sum(o.amount)" in col.lower() for col in result.selected_columns
    )
    assert "c.customer_name" in result.group_by_columns
    assert result.where_clause is not None
    assert result.having_clause is not None
    assert "sum" in result.aggregate_functions


def test_sqlglot_extracts_aliases_and_join_keys():
    sql = """
    select *
    from orders o
    left join customers c
        on o.customer_id = c.customer_id
       and o.region_id = c.region_id
    """

    result = analyze_with_sqlglot(sql)

    assert result.parse_error is None
    assert "o" in result.table_aliases
    assert "c" in result.table_aliases
    assert "o.customer_id = c.customer_id" in result.join_keys
    assert "o.region_id = c.region_id" in result.join_keys
