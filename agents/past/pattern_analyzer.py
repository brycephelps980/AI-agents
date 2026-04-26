from datetime import datetime
from loguru import logger

from agents.base_agent import BaseAgent
from orchestrator.run_context import AgentResult, RunContext
from tools.file_tools import (
    obsidian_read, obsidian_list_notes,
    OBSIDIAN_READ_TOOL, OBSIDIAN_LIST_TOOL,
    set_active_context,
)
from formatters.markdown import agent_note_header

TOOLS = [OBSIDIAN_LIST_TOOL, OBSIDIAN_READ_TOOL]
TOOL_REGISTRY = {
    "obsidian_list_notes": obsidian_list_notes,
    "obsidian_read": obsidian_read,
}


class PatternAnalyzerAgent(BaseAgent):
    name = "pattern_analyzer"
    tier = "past"
    SYSTEM_PROMPT = """\
You are the Pattern Analyzer agent. You receive a memory summary from the Memory Keeper \
and analyse it to identify:
1. Recurring themes across multiple days
2. Topics gaining momentum (mentioned more frequently over time)
3. Research gaps — important topics that have not been covered yet
4. Successful strategies or content types that worked well
5. Predictions: based on the past patterns, what topics are likely to be important today?

Output a structured markdown report with clear sections for each of the above points.\
"""

    def run(self, context: RunContext) -> AgentResult:
        set_active_context(context)

        past_tr = context.tier_results.get("past")
        memory_summary = ""
        if past_tr and "memory_keeper" in past_tr.agents:
            memory_summary = past_tr.agents["memory_keeper"].summary

        user_msg = (
            f"Today is {context.run_date.isoformat()}.\n\n"
            f"Here is the Memory Keeper's summary of the past 7 days:\n\n{memory_summary}\n\n"
            f"Please perform a pattern analysis as described in your instructions."
        )

        logger.info("[pattern_analyzer] starting run")
        analysis = self._run_agentic_loop(
            initial_messages=[{"role": "user", "content": user_msg}],
            tools=TOOLS,
            tool_registry=TOOL_REGISTRY,
        )

        note_title = f"{context.run_date.isoformat()} Pattern Analysis"
        header = agent_note_header(note_title, context.run_date, self.tier, self.name,
                                   tags=["patterns", "analysis"])
        note_content = header + "\n" + analysis
        note_path = f"Past/{note_title}.md"
        context.stage_output(note_path, note_content, self.name, self.tier)

        logger.info(f"[pattern_analyzer] staged {note_path}")
        return AgentResult(
            agent_name=self.name,
            tier=self.tier,
            run_at=datetime.utcnow(),
            summary=analysis[:500],
            outputs=[{"type": "pattern_analysis", "content": analysis}],
            obsidian_files=[note_path],
            errors=[],
        )
