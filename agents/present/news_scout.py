from datetime import datetime
from loguru import logger

from agents.base_agent import BaseAgent
from orchestrator.run_context import AgentResult, RunContext
from tools.web_search import web_search, WEB_SEARCH_TOOL
from tools.file_tools import stage_write, STAGE_WRITE_TOOL, set_active_context
from formatters.markdown import agent_note_header
from utils.config import get_config

TOOLS = [WEB_SEARCH_TOOL, STAGE_WRITE_TOOL]
TOOL_REGISTRY = {"web_search": web_search, "stage_write": stage_write}


class NewsScoutAgent(BaseAgent):
    name = "news_scout"
    tier = "present"
    SYSTEM_PROMPT = """\
You are the News Scout agent. Your job is to scan the internet for today's most relevant \
news and trending topics. You have access to web_search and stage_write tools.

Steps:
1. Run multiple web searches using the provided queries.
2. Identify the top 10 most interesting/relevant news items across technology, AI, science, \
   and any other topics the user cares about.
3. For each item write a 1–2 sentence summary.
4. Identify the 5 most significant trending topics today.
5. Write a well-formatted Obsidian markdown note using stage_write. Include YAML frontmatter \
   with title, date, tags, agent, created_by fields. Use ## headings for sections.

The note path should be: Present/YYYY-MM-DD News Scout.md\
"""

    def run(self, context: RunContext) -> AgentResult:
        set_active_context(context)
        cfg = get_config()
        queries = cfg.agents.news_scout.search_queries
        past_summary = context.get_tier_summary("past")

        user_msg = (
            f"Today is {context.run_date.isoformat()}.\n"
            f"Search queries to run: {queries}\n"
            f"Topics of interest: {context.topics_of_interest}\n"
        )
        if past_summary:
            user_msg += f"\nContext from memory analysis:\n{past_summary[:800]}\n"
        user_msg += "\nPlease scout today's news and write the note."

        logger.info("[news_scout] starting run")
        output = self._run_agentic_loop(
            initial_messages=[{"role": "user", "content": user_msg}],
            tools=TOOLS,
            tool_registry=TOOL_REGISTRY,
        )

        note_path = f"Present/{context.run_date.isoformat()} News Scout.md"
        staged = [s for s in context.staged_outputs if s.agent_name == self.name]

        logger.info(f"[news_scout] staged {len(staged)} file(s)")
        return AgentResult(
            agent_name=self.name,
            tier=self.tier,
            run_at=datetime.utcnow(),
            summary=output[:500],
            outputs=[{"type": "news_summary", "content": output}],
            obsidian_files=[note_path],
            errors=[],
        )
