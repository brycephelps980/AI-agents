from __future__ import annotations

from loguru import logger
from agents.base_agent import BaseAgent
from orchestrator.run_context import AgentResult, TierResult, RunContext


class TierOrchestrator:
    tier: str = "base"

    def __init__(self, agents: list[BaseAgent]) -> None:
        self.agents = agents

    def run(self, context: RunContext) -> TierResult:
        result = TierResult(tier=self.tier)
        context.tier_results[self.tier] = result

        for agent in self.agents:
            logger.info(f"[{self.tier}_orchestrator] running {agent.name}")
            ar = agent.run_with_timeout(context)
            result.agents[agent.name] = ar
            if ar.errors:
                logger.warning(f"[{self.tier}_orchestrator] {agent.name} errors: {ar.errors}")

        result.tier_summary = self._build_summary(result)
        return result

    def _build_summary(self, result: TierResult) -> str:
        parts = []
        for ar in result.agents.values():
            if ar.summary:
                parts.append(f"**{ar.agent_name}**: {ar.summary[:200]}")
        return "\n".join(parts)
