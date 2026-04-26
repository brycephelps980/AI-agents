from agents.present.news_scout import NewsScoutAgent
from agents.present.research_assistant import ResearchAssistantAgent
from agents.present.task_manager import TaskManagerAgent
from orchestrator.tier_orchestrator import TierOrchestrator


class PresentOrchestrator(TierOrchestrator):
    tier = "present"

    def __init__(self) -> None:
        # NewsScout → ResearchAssistant → TaskManager (sequential dependency)
        super().__init__([NewsScoutAgent(), ResearchAssistantAgent(), TaskManagerAgent()])
