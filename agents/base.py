from abc import ABC, abstractmethod
from typing import Any

import structlog

from shared.schemas.agent_outputs import AgentInsight

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    name: str = "BaseAgent"
    description: str = ""

    def __init__(self) -> None:
        self.logger = logger.bind(agent=self.name)

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        ...

    def _create_insight(
        self,
        reasoning: str,
        confidence: float,
        evidence: list[str] | None = None,
        **kwargs: Any,
    ) -> AgentInsight:
        return AgentInsight(
            agent_name=self.name,
            reasoning=reasoning,
            confidence=confidence,
            evidence=evidence or [],
            policy_references=kwargs.get("policy_references", []),
            contract_clauses=kwargs.get("contract_clauses", []),
            suggested_resolution=kwargs.get("suggested_resolution", ""),
            business_impact=kwargs.get("business_impact", ""),
            financial_impact=kwargs.get("financial_impact", 0),
            estimated_loss=kwargs.get("estimated_loss", 0),
            next_action=kwargs.get("next_action", ""),
            metadata=kwargs.get("metadata", {}),
        )
