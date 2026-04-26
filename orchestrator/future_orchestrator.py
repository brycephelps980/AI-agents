from agents.future.goal_planner import GoalPlannerAgent
from agents.future.content_strategist import ContentStrategistAgent
from agents.future.trend_forecaster import TrendForecasterAgent
from orchestrator.tier_orchestrator import TierOrchestrator


class FutureOrchestrator(TierOrchestrator):
    tier = "future"

    def __init__(self) -> None:
        super().__init__([GoalPlannerAgent(), ContentStrategistAgent(), TrendForecasterAgent()])
