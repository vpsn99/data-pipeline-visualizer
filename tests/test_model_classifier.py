from app.model_classifier import classify_model_layer


def test_classify_model_layer():
    assert classify_model_layer("src_orders") == "source"
    assert classify_model_layer("stg_orders") == "staging"
    assert classify_model_layer("int_sales") == "intermediate"
    assert classify_model_layer("dim_customer") == "dimension"
    assert classify_model_layer("fct_sales") == "fact"
    assert classify_model_layer("agg_monthly_sales") == "aggregate"
    assert classify_model_layer("orders") == "other"
