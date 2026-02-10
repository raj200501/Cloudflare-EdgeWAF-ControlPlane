from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class RuleCondition(BaseModel):
    field: Literal["path", "query", "body", "headers", "method", "user_agent"]
    pattern: str
    operator: Literal["contains", "regex"] = "contains"


class RuleAction(BaseModel):
    action: Literal["allow", "block"]
    reason: str
    threat_type: Optional[str] = None


class Rule(BaseModel):
    id: str
    description: str
    tags: list[str] = Field(default_factory=list)
    priority: int = 100
    condition: RuleCondition
    action: RuleAction


class Ruleset(BaseModel):
    name: str
    rules: list[Rule]
