"""
SafetyGuardianAgent — reviews ALL staged outputs before any disk write.
This agent is the last line of defence before content reaches the Obsidian vault.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from loguru import logger

from agents.base_agent import BaseAgent
from orchestrator.run_context import AgentResult, RunContext, StagedOutput
from utils.config import get_config
from utils.safety import redact_secrets, contains_secret


GUARDIAN_SYSTEM_PROMPT = """\
You are the Safety Guardian agent. Your sole purpose is to protect the user by reviewing \
AI-generated content BEFORE it is written to their Obsidian vault.

You will receive a list of staged file outputs. For each file you must respond with a \
JSON array of review decisions. Each decision has this structure:
{
  "relative_path": "<path>",
  "decision": "approve" | "redact" | "block",
  "reason": "<brief reason, required for redact/block>",
  "redacted_content": "<full content after redaction, required only if decision is redact>"
}

Rules for decisions:
- "approve": Content is helpful, accurate, and safe. No issues found.
- "redact": Content is mostly fine but contains specific problematic text that should be \
  removed or replaced. Provide the full corrected content in redacted_content.
- "block": Content is fundamentally unsafe, harmful, or critically incorrect and should \
  not be written at all.

You should BLOCK content that:
- Contains instructions for illegal activities or causing harm to people
- Contains real personal data (names + addresses, phone numbers, SSNs, etc.)
- Contains exposed API keys, passwords, or security credentials (even if partially shown)

You should REDACT content that:
- Contains mildly sensitive information that can be safely removed
- References clearly fabricated "facts" with made-up URLs or statistics

You should APPROVE content that:
- Is helpful research, news summaries, task management, or creative content ideas
- May contain controversial but legal opinions or information
- Is imperfect but not dangerous

Be permissive — your role is safety, not censorship. When in doubt, approve.\
"""


class SafetyGuardianAgent(BaseAgent):
    name = "safety_guardian"
    tier = "safety"
    SYSTEM_PROMPT = GUARDIAN_SYSTEM_PROMPT

    def run(self, context: RunContext) -> AgentResult:
        cfg = get_config()
        pending = [s for s in context.staged_outputs if not s.blocked]

        if not pending:
            logger.info("[safety_guardian] no staged outputs to review")
            return AgentResult(
                agent_name=self.name,
                tier=self.tier,
                run_at=datetime.utcnow(),
                summary="No outputs to review.",
                outputs=[],
                obsidian_files=[],
                errors=[],
            )

        # Pre-scan for secrets before sending to the model
        for item in pending:
            if contains_secret(item.content, cfg.safety.secret_patterns):
                logger.warning(f"[safety_guardian] pre-scan: secret detected in {item.relative_path} — redacting")
                item.content = redact_secrets(item.content, cfg.safety.secret_patterns)

        # Build review request
        files_payload = json.dumps([
            {"relative_path": s.relative_path, "content": s.content[:8000]}
            for s in pending
        ], indent=2)

        user_msg = (
            f"Please review the following {len(pending)} staged file(s) and return "
            f"a JSON array of decisions.\n\nStaged files:\n{files_payload}"
        )

        logger.info(f"[safety_guardian] reviewing {len(pending)} staged outputs")
        raw_response = self._run_agentic_loop(
            initial_messages=[{"role": "user", "content": user_msg}],
            tools=[],
            tool_registry={},
        )

        # Parse decisions
        decisions = self._parse_decisions(raw_response, pending)
        approved = redacted = blocked = 0

        for item in pending:
            decision = decisions.get(item.relative_path, {})
            action = decision.get("decision", "approve")

            if action == "block":
                item.blocked = True
                item.block_reason = decision.get("reason", "blocked by safety guardian")
                blocked += 1
                logger.warning(f"[safety_guardian] BLOCKED: {item.relative_path} — {item.block_reason}")

            elif action == "redact":
                new_content = decision.get("redacted_content", item.content)
                if new_content:
                    item.content = new_content
                item.redacted = True
                item.approved = True
                redacted += 1
                logger.info(f"[safety_guardian] REDACTED: {item.relative_path}")

            else:
                item.approved = True
                approved += 1
                logger.debug(f"[safety_guardian] approved: {item.relative_path}")

        # Write safety report
        report = self._build_safety_report(context, approved, redacted, blocked, decisions)
        context.stage_output(
            f"Safety/{context.run_date.isoformat()} Safety Report.md",
            report,
            self.name,
            self.tier,
        )
        # The safety report approves itself
        safety_report_item = context.staged_outputs[-1]
        safety_report_item.approved = True

        summary = f"Reviewed {len(pending)} files: {approved} approved, {redacted} redacted, {blocked} blocked."
        logger.info(f"[safety_guardian] {summary}")

        return AgentResult(
            agent_name=self.name,
            tier=self.tier,
            run_at=datetime.utcnow(),
            summary=summary,
            outputs=[{"approved": approved, "redacted": redacted, "blocked": blocked}],
            obsidian_files=[f"Safety/{context.run_date.isoformat()} Safety Report.md"],
            errors=[],
        )

    def _parse_decisions(self, raw: str, pending: list[StagedOutput]) -> dict:
        # Extract JSON array from response
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if not match:
            logger.warning("[safety_guardian] could not parse JSON decisions — approving all")
            return {}
        try:
            items = json.loads(match.group())
            return {item["relative_path"]: item for item in items if "relative_path" in item}
        except Exception as e:
            logger.warning(f"[safety_guardian] JSON parse error: {e} — approving all")
            return {}

    def _build_safety_report(self, context: RunContext, approved: int,
                              redacted: int, blocked: int, decisions: dict) -> str:
        from formatters.markdown import build_frontmatter, h1, h2
        fm = build_frontmatter({
            "title": f"Safety Report — {context.run_date.isoformat()}",
            "date": context.run_date.isoformat(),
            "tags": ["safety", "ai-agents", "audit"],
            "agent": self.name,
            "run_id": context.run_id,
            "created_by": "ai-agents-system",
        })
        lines = [fm, "", h1(f"Safety Report — {context.run_date.isoformat()}"), ""]
        lines.append(f"**Total reviewed:** {approved + redacted + blocked}  ")
        lines.append(f"**Approved:** {approved}  ")
        lines.append(f"**Redacted:** {redacted}  ")
        lines.append(f"**Blocked:** {blocked}  ")
        lines.append("")
        if blocked or redacted:
            lines.append(h2("Issues Found"))
            for path, d in decisions.items():
                if d.get("decision") in ("block", "redact"):
                    lines.append(f"- **{d['decision'].upper()}** `{path}`: {d.get('reason', '')}")
        else:
            lines.append("> All outputs passed safety review with no issues.")
        return "\n".join(lines)
