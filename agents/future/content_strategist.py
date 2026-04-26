from datetime import datetime
from loguru import logger

from agents.base_agent import BaseAgent
from orchestrator.run_context import AgentResult, RunContext
from tools.web_search import web_search, WEB_SEARCH_TOOL
from tools.file_tools import stage_write, STAGE_WRITE_TOOL, set_active_context
from utils.config import get_config

TOOLS = [WEB_SEARCH_TOOL, STAGE_WRITE_TOOL]
TOOL_REGISTRY = {"web_search": web_search, "stage_write": stage_write}


class ContentStrategistAgent(BaseAgent):
    name = "content_strategist"
    tier = "future"
    SYSTEM_PROMPT = """\
You are the Content Strategist agent. You create a content calendar and content ideas \
grounded in today's research, news, and trends.

Steps:
1. Review the provided context (news, research, patterns).
2. If needed, use web_search to verify what content is trending in the user's topic areas.
3. Generate content ideas for the user's platforms (blog, twitter, youtube, etc.).
4. For each idea provide: title, format, key angle, why it's timely, estimated effort (low/medium/high).
5. Write a content calendar note using stage_write at: Future/YYYY-MM-DD Content Calendar.md

Structure: ## Content Ideas (with platform tags), ## Weekly Calendar (Mon–Sun schedule), \
## Evergreen Backlog\
"""

    def run(self, context: RunContext) -> AgentResult:
        set_active_context(context)
        cfg = get_config()
        platforms = cfg.agents.content_strategist.platforms
        ideas_count = cfg.agents.content_strategist.ideas_per_run
        all_context = context.all_prior_summaries("safety")

        user_msg = (
            f"Today is {context.run_date.isoformat()}.\n"
            f"Target platforms: {platforms}\n"
            f"Generate {ideas_count} content ideas.\n\n"
            f"Context from today's research:\n{all_context[:1200]}\n\n"
            "Please create the content strategy note."
        )

        logger.info("[content_strategist] starting run")
        output = self._run_agentic_loop(
            initial_messages=[{"role": "user", "content": user_msg}],
            tools=TOOLS,
            tool_registry=TOOL_REGISTRY,
        )

        staged = [s for s in context.staged_outputs if s.agent_name == self.name]
        logger.info(f"[content_strategist] staged {len(staged)} file(s)")
        return AgentResult(
            agent_name=self.name,
            tier=self.tier,
            run_at=datetime.utcnow(),
            summary=output[:500],
            outputs=[{"type": "content_calendar", "content": output}],
            obsidian_files=[s.relative_path for s in staged],
            errors=[],
        )
