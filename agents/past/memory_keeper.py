from datetime import datetime, date, timedelta
from loguru import logger

from agents.base_agent import BaseAgent
from orchestrator.run_context import AgentResult, RunContext
from tools.file_tools import (
    obsidian_read, obsidian_list_notes,
    OBSIDIAN_READ_TOOL, OBSIDIAN_LIST_TOOL,
    set_active_context,
)
from formatters.markdown import agent_note_header, h2, callout

TOOLS = [OBSIDIAN_LIST_TOOL, OBSIDIAN_READ_TOOL]
TOOL_REGISTRY = {
    "obsidian_list_notes": obsidian_list_notes,
    "obsidian_read": obsidian_read,
}


class MemoryKeeperAgent(BaseAgent):
    name = "memory_keeper"
    tier = "past"
    SYSTEM_PROMPT = """\
You are the Memory Keeper agent. Your job is to read the AI-Agents Obsidian vault notes \
from the past 7 days and produce a concise knowledge summary that will be used by other agents \
running today.

Steps:
1. Use obsidian_list_notes to find recent notes in each tier subfolder (Past, Present, Future).
2. Use obsidian_read to read the most relevant notes (prioritise Daily Briefings and Research notes).
3. Synthesise a structured summary covering:
   - Key topics researched recently
   - Open questions or knowledge gaps
   - Recurring themes
   - Any important tasks or goals mentioned

Output your summary in markdown. Be concise but thorough — this is context for today's run.\
"""

    def run(self, context: RunContext) -> AgentResult:
        set_active_context(context)
        cfg_days = context.topics_of_interest  # used for relevance filtering

        cutoff = (context.run_date - timedelta(days=7)).isoformat()
        user_msg = (
            f"Today is {context.run_date.isoformat()}. "
            f"Please review Obsidian notes from the past 7 days (since {cutoff}) "
            f"and produce a knowledge summary. Focus on these topics if present: "
            f"{', '.join(context.topics_of_interest)}."
        )

        logger.info("[memory_keeper] starting run")
        summary = self._run_agentic_loop(
            initial_messages=[{"role": "user", "content": user_msg}],
            tools=TOOLS,
            tool_registry=TOOL_REGISTRY,
        )

        note_title = f"{context.run_date.isoformat()} Memory Summary"
        header = agent_note_header(note_title, context.run_date, self.tier, self.name,
                                   tags=["memory", "summary"])
        note_content = header + "\n" + summary
        note_path = f"Past/{note_title}.md"
        context.stage_output(note_path, note_content, self.name, self.tier)

        logger.info(f"[memory_keeper] staged {note_path}")
        return AgentResult(
            agent_name=self.name,
            tier=self.tier,
            run_at=datetime.utcnow(),
            summary=summary[:500],
            outputs=[{"type": "memory_summary", "content": summary}],
            obsidian_files=[note_path],
            errors=[],
        )
