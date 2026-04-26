from datetime import datetime
from loguru import logger

from agents.base_agent import BaseAgent
from orchestrator.run_context import AgentResult, RunContext
from tools.todo_tools import (
    todo_read, todo_write, todo_complete, todo_update,
    TODO_READ_TOOL, TODO_WRITE_TOOL, TODO_COMPLETE_TOOL, TODO_UPDATE_TOOL,
)
from tools.file_tools import (
    stage_write, obsidian_read,
    STAGE_WRITE_TOOL, OBSIDIAN_READ_TOOL,
    set_active_context,
)
from utils.config import get_config

TOOLS = [TODO_READ_TOOL, TODO_WRITE_TOOL, TODO_COMPLETE_TOOL, TODO_UPDATE_TOOL,
         OBSIDIAN_READ_TOOL, STAGE_WRITE_TOOL]
TOOL_REGISTRY = {
    "todo_read": todo_read,
    "todo_write": todo_write,
    "todo_complete": todo_complete,
    "todo_update": todo_update,
    "obsidian_read": obsidian_read,
    "stage_write": stage_write,
}


class TaskManagerAgent(BaseAgent):
    name = "task_manager"
    tier = "present"
    SYSTEM_PROMPT = """\
You are the Task Manager agent. You manage the user's to-do list with care and intelligence.

Steps:
1. Use todo_read to get all open tasks.
2. Review due dates — flag anything due within 2 days as urgent.
3. Based on today's research (provided in context), use todo_write to create any new relevant tasks.
4. If any tasks are clearly outdated or no longer relevant, use todo_update to update their status.
5. Write a concise tasks summary note using stage_write at: Present/Tasks/todos.md
   Include sections: ## Urgent, ## Today's Priorities, ## Upcoming, ## New Tasks Created

Keep your task management helpful and proactive, not overwhelming.\
"""

    def run(self, context: RunContext) -> AgentResult:
        set_active_context(context)
        cfg = get_config()

        present_context = context.all_prior_summaries("future")
        user_msg = (
            f"Today is {context.run_date.isoformat()}.\n"
            f"Reminder days ahead setting: {cfg.agents.task_manager.reminder_days_ahead}\n"
        )
        if present_context:
            user_msg += f"\nContext from today's research:\n{present_context[:600]}\n"
        user_msg += "\nPlease review and manage the to-do list."

        logger.info("[task_manager] starting run")
        output = self._run_agentic_loop(
            initial_messages=[{"role": "user", "content": user_msg}],
            tools=TOOLS,
            tool_registry=TOOL_REGISTRY,
        )

        staged = [s for s in context.staged_outputs if s.agent_name == self.name]
        logger.info(f"[task_manager] staged {len(staged)} file(s)")
        return AgentResult(
            agent_name=self.name,
            tier=self.tier,
            run_at=datetime.utcnow(),
            summary=output[:500],
            outputs=[{"type": "task_summary", "content": output}],
            obsidian_files=[s.relative_path for s in staged],
            errors=[],
        )
