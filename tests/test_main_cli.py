from app.main import resolve_sqlglot_usage


def test_resolve_sqlglot_usage():
    assert resolve_sqlglot_usage("heuristic") is False
    assert resolve_sqlglot_usage("sqlglot") is True
    assert resolve_sqlglot_usage("auto") is True
