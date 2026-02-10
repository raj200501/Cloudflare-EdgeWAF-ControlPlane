from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .models import Rule, Ruleset

SAFE_REGEX_FLAGS = re.IGNORECASE


@dataclass
class RuleMatch:
    action: str
    reason: str
    threat_type: Optional[str]
    rule_id: Optional[str]


class RuleEngine:
    def __init__(self, ruleset: Ruleset):
        self.ruleset = ruleset
        self._rules = sorted(ruleset.rules, key=lambda rule: rule.priority)

    @classmethod
    def from_json(cls, path: str | Path) -> "RuleEngine":
        data = json.loads(Path(path).read_text())
        ruleset = Ruleset.model_validate(data)
        return cls(ruleset)

    def evaluate(self, request: dict[str, Any]) -> RuleMatch:
        for rule in self._rules:
            if self._match_rule(rule, request):
                return RuleMatch(
                    action=rule.action.action,
                    reason=rule.action.reason,
                    threat_type=rule.action.threat_type,
                    rule_id=rule.id,
                )
        return RuleMatch(action="allow", reason="ok", threat_type=None, rule_id=None)

    def _match_rule(self, rule: Rule, request: dict[str, Any]) -> bool:
        condition = rule.condition
        value = self._get_value(condition.field, request)
        if value is None:
            return False
        pattern = condition.pattern
        if condition.operator == "contains":
            return pattern.lower() in str(value).lower()
        if condition.operator == "regex":
            return re.search(pattern, str(value), SAFE_REGEX_FLAGS) is not None
        return False

    @staticmethod
    def _get_value(field: str, request: dict[str, Any]) -> Any:
        if field == "user_agent":
            return request.get("headers", {}).get("user-agent")
        return request.get(field)
