"""
Root OrchestratorAgent — runs all three tiers, calls the SafetyGuardian,
commits approved outputs to the Obsidian vault, and writes the Daily Briefing.
"""
from __future__ import annotations

from datetime import date
from loguru import logger

from orchestrator.run_context import RunContext
from orchestrator.past_orchestrator import PastOrchestrator
from orchestrator.present_orchestrator import PresentOrchestrator
from orchestrator.future_orchestrator import FutureOrchestrator
from agents.safety.safety_guardian import SafetyGuardianAgent
from integrations.obsidian import get_writer
from formatters.daily_briefing import build_daily_briefing
from storage import state_store
from utils.config import get_config
from tools.file_tools import set_active_context, clear_active_context


class RootOrchestrator:
    def __init__(self) -> None:
        self.past = PastOrchestrator()
        self.present = PresentOrchestrator()
        self.future = FutureOrchestrator()
        self.guardian = SafetyGuardianAgent()

    def _build_context(self) -> RunContext:
        cfg = get_config()
        return RunContext(
            run_date=date.today(),
            topics_of_interest=cfg.agents.topics_of_interest,
        )

    def run_full_pipeline(self) -> RunContext:
        context = self._build_context()
        set_active_context(context)
        logger.info(f"=== Run started: {context.run_id[:8]} | {context.run_date} ===")

        try:
            # Tier execution: Past → Present → Future
            logger.info("--- PAST TIER ---")
            self.past.run(context)

            logger.info("--- PRESENT TIER ---")
            self.present.run(context)

            logger.info("--- FUTURE TIER ---")
            self.future.run(context)

            # Safety review
            logger.info("--- SAFETY REVIEW ---")
            guardian_result = self.guardian.run_with_timeout(context)
            context.tier_results["safety"] = type(
                "TierResult", (), {
                    "tier": "safety",
                    "agents": {"safety_guardian": guardian_result},
                    "tier_summary": guardian_result.summary,
                }
            )()

            # Commit approved outputs to vault
            self._commit_outputs(context)

            # Write Daily Briefing
            self._write_daily_briefing(context)

            # Persist run state
            state_store.set_last_run(context.run_id)

            elapsed = context.elapsed_seconds()
            logger.info(f"=== Run complete in {elapsed:.1f}s: {context.run_id[:8]} ===")

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise
        finally:
            clear_active_context()

        return context

    def run_tier(self, tier: str) -> RunContext:
        context = self._build_context()
        set_active_context(context)
        try:
            tier_map = {"past": self.past, "present": self.present, "future": self.future}
            orchestrator = tier_map.get(tier)
            if not orchestrator:
                raise ValueError(f"Unknown tier: {tier}")
            orchestrator.run(context)
            self.guardian.run_with_timeout(context)
            self._commit_outputs(context)
        finally:
            clear_active_context()
        return context

    def run_agent(self, agent_name: str) -> RunContext:
        context = self._build_context()
        set_active_context(context)
        agent = self._find_agent(agent_name)
        if agent is None:
            raise ValueError(f"Unknown agent: {agent_name}")
        try:
            result = agent.run_with_timeout(context)
            # For single-agent runs, approve all outputs and commit without guardian
            for item in context.staged_outputs:
                item.approved = True
            self._commit_outputs(context)
            logger.info(f"Single-agent run complete: {agent_name}")
        finally:
            clear_active_context()
        return context

    def _commit_outputs(self, context: RunContext) -> None:
        writer = get_writer()
        approved = [s for s in context.staged_outputs if s.approved and not s.blocked]
        for item in approved:
            writer.write(item.relative_path, item.content)
            logger.debug(f"Committed: {item.relative_path}")
        blocked = [s for s in context.staged_outputs if s.blocked]
        if blocked:
            logger.warning(f"Skipped {len(blocked)} blocked output(s)")

    def _write_daily_briefing(self, context: RunContext) -> None:
        writer = get_writer()
        briefing = build_daily_briefing(context)
        path = f"Daily Briefings/{context.run_date.isoformat()} Daily Briefing.md"
        writer.write(path, briefing)
        logger.info(f"Daily Briefing written: {path}")

    def _find_agent(self, name: str):
        all_agents = [
            *self.past.agents,
            *self.present.agents,
            *self.future.agents,
            self.guardian,
        ]
        return next((a for a in all_agents if a.name == name), None)
