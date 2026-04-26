from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class AgentResult:
    agent_name: str
    tier: str
    run_at: datetime
    summary: str
    outputs: list[dict]
    obsidian_files: list[str]
    errors: list[str]


@dataclass
class StagedOutput:
    relative_path: str
    content: str
    agent_name: str
    tier: str
    # Set by SafetyGuardian after review
    approved: bool = False
    redacted: bool = False
    blocked: bool = False
    block_reason: str = ""


@dataclass
class TierResult:
    tier: str
    agents: dict[str, AgentResult] = field(default_factory=dict)
    tier_summary: str = ""


@dataclass
class RunContext:
    run_date: date
    topics_of_interest: list[str]
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tier_results: dict[str, TierResult] = field(default_factory=dict)
    staged_outputs: list[StagedOutput] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)

    def stage_output(self, relative_path: str, content: str,
                     agent_name: str = "unknown", tier: str = "unknown") -> None:
        self.staged_outputs.append(
            StagedOutput(
                relative_path=relative_path,
                content=content,
                agent_name=agent_name,
                tier=tier,
            )
        )

    def get_tier_summary(self, tier: str) -> str:
        tr = self.tier_results.get(tier)
        return tr.tier_summary if tr else ""

    def all_prior_summaries(self, before_tier: str) -> str:
        order = ["past", "present", "future"]
        summaries = []
        for t in order:
            if t == before_tier:
                break
            tr = self.tier_results.get(t)
            if tr and tr.tier_summary:
                summaries.append(f"### {t.capitalize()} Tier\n{tr.tier_summary}")
        return "\n\n".join(summaries)

    def elapsed_seconds(self) -> float:
        return (datetime.utcnow() - self.start_time).total_seconds()
