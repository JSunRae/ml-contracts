from promotion_rules import evaluate_rule


def test_other_operators():
    manifest = {
        "metrics": {
            "a": {"value": 1.0},
            "b": {"value": 2.0}
        },
        "latency_metrics": {
            "p95_ms": {"value": 2.0}
        }
    }
    # >=
    assert evaluate_rule({">=": [{"var": "metrics.a.value"}, 1.0]}, manifest)
    # >
    assert evaluate_rule({">": [{"var": "metrics.b.value"}, 1.5]}, manifest)
    # <
    assert evaluate_rule({"<": [{"var": "latency_metrics.p95_ms.value"}, 3]}, manifest)
    # <=
    assert evaluate_rule({"<=": [{"var": "metrics.a.value"}, 1.0]}, manifest)