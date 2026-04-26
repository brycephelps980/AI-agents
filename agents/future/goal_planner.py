from datetime import datetime
from loguru import logger

from agents.base_agent import BaseAgent
from orchestrator.run_context import AgentResult, RunContext
from tools.file_tools import (
    stage_write, obsidian_read, obsidian_list_notes,
    STAGE_WRITE_TOOL, OBSIDIAN_READ_TOOL, OBSIDIAN_LIST_TOOL,
    set_active_context,
)
from tools.todo_tools import todo_write, TODO_WRITE_TOOL

TOOLS = [OBSIDIAN_LIST_TOOL, OBSIDIAN_READ_TOOL, STAGE_WRITE_TOOL, TODO_WRITE_TOOL]
TOOL_REGISTRY = {
    "obsidian_list_notes": obsidian_list_notes,
    "obsidian_read": obsidian_read,
    "stage_write": stage_write,
    "todo_write": todo_write,
}


class GoalPlannerAgent(BaseAgent):
    name = "goal_planner"
    tier = "future"
    SYSTEM_PROMPT = """\
You are the Goal Planner agent. You help the user stay on track with their long-term goals \
by reviewing progress and suggesting concrete next steps.

Steps:
1. Use obsidian_list_notes to find any existing goal or planning notes.
2. Use obsidian_read to review them.
3. Cross-reference with today's research findings (provided in context).
4. Identify which goals have momentum and which are stalled.
5. Suggest 3–5 concrete, actionable next steps for the coming week.
6. Use todo_write to create high-priority tasks for the top next steps.
7. Write a goal review note using stage_write at: Future/YYYY-MM-DD Goal Review.md

Structure the note with: ## Long-term Goals Status, ## Next Steps, ## Newly Created Tasks\
"""

    def run(self, context: RunContext) -> AgentResult:
        set_active_context(context)
        all_context = context.all_prior_summaries("safety")

        user_msg = (
            f"Today is {context.run_date.isoformat()}.\n"
            f"Here is what the other agents found today:\n{all_context[:1200]}\n\n"
            "Please review goals and plan next steps."
        )

        logger.info("[goal_planner] starting run")
        output = self._run_agentic_loop(
            initial_messages=[{"role": "user", "content": user_msg}],
            tools=TOOLS,
            tool_registry=TOOL_REGISTRY,
        )

        staged = [s for s in context.staged_outputs if s.agent_name == self.name]
        logger.info(f"[goal_planner] staged {len(staged)} file(s)")
        return AgentResult(
            agent_name=self.name,
            tier=self.tier,
            run_at=datetime.utcnow(),
            summary=output[:500],
            outputs=[{"type": "goal_review", "content": output}],
            obsidian_files=[s.relative_path for s in staged],
            errors=[],
        )
