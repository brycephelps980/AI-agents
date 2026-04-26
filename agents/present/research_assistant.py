from datetime import datetime
from loguru import logger

from agents.base_agent import BaseAgent
from orchestrator.run_context import AgentResult, RunContext
from tools.web_search import web_search, WEB_SEARCH_TOOL
from tools.file_tools import (
    stage_write, obsidian_read, obsidian_list_notes,
    STAGE_WRITE_TOOL, OBSIDIAN_READ_TOOL, OBSIDIAN_LIST_TOOL,
    set_active_context,
)
from tools.todo_tools import todo_write, TODO_WRITE_TOOL
from utils.config import get_config

TOOLS = [WEB_SEARCH_TOOL, OBSIDIAN_READ_TOOL, OBSIDIAN_LIST_TOOL, STAGE_WRITE_TOOL, TODO_WRITE_TOOL]
TOOL_REGISTRY = {
    "web_search": web_search,
    "obsidian_read": obsidian_read,
    "obsidian_list_notes": obsidian_list_notes,
    "stage_write": stage_write,
    "todo_write": todo_write,
}


class ResearchAssistantAgent(BaseAgent):
    name = "research_assistant"
    tier = "present"
    SYSTEM_PROMPT = """\
You are the Research Assistant agent. You perform deep research on given topics and \
write comprehensive, well-sourced Obsidian notes.

For each topic assigned to you:
1. Use obsidian_list_notes to check if research on this topic already exists recently.
2. If it does, use obsidian_read to review it and only add new findings.
3. Use web_search (multiple searches if needed) to gather current information.
4. Write a research note using stage_write with:
   - YAML frontmatter (title, date, tags, agent, topic, sources, created_by)
   - ## Summary section (3–5 sentences)
   - ## Key Findings section (bullet points)
   - ## Sources section (list of URLs)
5. If you identify a follow-up research task, use todo_write to create it.

Note paths: Present/YYYY-MM-DD Research — <Topic>.md\
"""

    def run(self, context: RunContext) -> AgentResult:
        set_active_context(context)
        cfg = get_config()
        max_topics = cfg.agents.research_assistant.max_topics_per_run

        # Gather topics from config + any trending topics from NewsScout
        topics = list(context.topics_of_interest[:max_topics])
        past_summary = context.get_tier_summary("past")
        present_so_far = context.all_prior_summaries("future")

        user_msg = (
            f"Today is {context.run_date.isoformat()}.\n"
            f"Research topics (up to {max_topics}): {topics}\n"
        )
        if past_summary:
            user_msg += f"\nPast tier context:\n{past_summary[:600]}\n"
        if present_so_far:
            user_msg += f"\nPresent tier context so far:\n{present_so_far[:400]}\n"
        user_msg += "\nPlease research each topic and write individual notes."

        logger.info("[research_assistant] starting run")
        output = self._run_agentic_loop(
            initial_messages=[{"role": "user", "content": user_msg}],
            tools=TOOLS,
            tool_registry=TOOL_REGISTRY,
        )

        staged = [s for s in context.staged_outputs if s.agent_name == self.name]
        logger.info(f"[research_assistant] staged {len(staged)} file(s)")
        return AgentResult(
            agent_name=self.name,
            tier=self.tier,
            run_at=datetime.utcnow(),
            summary=output[:500],
            outputs=[{"type": "research_output", "content": output}],
            obsidian_files=[s.relative_path for s in staged],
            errors=[],
        )
