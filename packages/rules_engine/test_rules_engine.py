from packages.rules_engine.engine import RuleEngine


def test_rules_engine_parses_and_matches(tmp_path):
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(
        """
        {"name": "test", "rules": [
            {"id": "1", "description": "SQL", "tags": ["sqli"], "priority": 1,
             "condition": {"field": "query", "pattern": "union select", "operator": "contains"},
             "action": {"action": "block", "reason": "sqli", "threat_type": "sql-injection"}}
        ]}
        """
    )
    engine = RuleEngine.from_json(rules_path)
    match = engine.evaluate({"query": "id=1 union select"})
    assert match.action == "block"
    assert match.reason == "sqli"
    assert match.rule_id == "1"


def test_rules_engine_precedence():
    engine = RuleEngine.from_json("packages/rules_engine/rules/default.json")
    match = engine.evaluate({"query": "<script>alert(1)</script>"})
    assert match.action == "block"
    assert match.reason == "xss"
