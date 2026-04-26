from datetime import datetime
from loguru import logger

from agents.base_agent import BaseAgent
from orchestrator.run_context import AgentResult, RunContext
from tools.web_search import web_search, WEB_SEARCH_TOOL
from tools.file_tools import stage_write, STAGE_WRITE_TOOL, set_active_context
from utils.config import get_config

TOOLS = [WEB_SEARCH_TOOL, STAGE_WRITE_TOOL]
TOOL_REGISTRY = {"web_search": web_search, "stage_write": stage_write}


class TrendForecasterAgent(BaseAgent):
    name = "trend_forecaster"
    tier = "future"
    SYSTEM_PROMPT = """\
You are the Trend Forecaster agent. You synthesise past patterns and present news to \
forecast emerging opportunities and topics over the coming 1–4 weeks.

Steps:
1. Review the provided context (memory patterns + today's news and research).
2. Use web_search to look for signals about emerging topics (search for "emerging trends", \
   upcoming events, scheduled announcements, etc. in relevant domains).
3. Identify 5–7 trends or opportunities worth watching.
4. For each, estimate: signal strength (weak/moderate/strong), expected timeline, \
   potential impact, and recommended action.
5. Write the forecast using stage_write at: Future/YYYY-MM-DD Trend Forecast.md

Structure: ## Executive Summary, ## Trend Signals (one sub-section per trend), \
## Recommended Actions\
"""

    def run(self, context: RunContext) -> AgentResult:
        set_active_context(context)
        cfg = get_config()
        weeks = cfg.agents.trend_forecaster.forecast_weeks_ahead
        all_context = context.all_prior_summaries("safety")

        user_msg = (
            f"Today is {context.run_date.isoformat()}. Forecast horizon: {weeks} weeks.\n\n"
            f"Full context from all agents today:\n{all_context[:1500]}\n\n"
            "Please produce the trend forecast."
        )

        logger.info("[trend_forecaster] starting run")
        output = self._run_agentic_loop(
            initial_messages=[{"role": "user", "content": user_msg}],
            tools=TOOLS,
            tool_registry=TOOL_REGISTRY,
        )

        staged = [s for s in context.staged_outputs if s.agent_name == self.name]
        logger.info(f"[trend_forecaster] staged {len(staged)} file(s)")
        return AgentResult(
            agent_name=self.name,
            tier=self.tier,
            run_at=datetime.utcnow(),
            summary=output[:500],
            outputs=[{"type": "trend_forecast", "content": output}],
            obsidian_files=[s.relative_path for s in staged],
            errors=[],
        )
