from agents.past.memory_keeper import MemoryKeeperAgent
from agents.past.pattern_analyzer import PatternAnalyzerAgent
from orchestrator.tier_orchestrator import TierOrchestrator
from orchestrator.run_context import RunContext, TierResult


class PastOrchestrator(TierOrchestrator):
    tier = "past"

    def __init__(self) -> None:
        # PatternAnalyzer depends on MemoryKeeper — order matters
        super().__init__([MemoryKeeperAgent(), PatternAnalyzerAgent()])
