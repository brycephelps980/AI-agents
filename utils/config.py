import os
from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, model_validator, field_validator


class ObsidianConfig(BaseModel):
    vault_path: str
    agent_folder: str = "AI-Agents"

    @field_validator("vault_path")
    @classmethod
    def vault_must_exist(cls, v: str) -> str:
        p = Path(v)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
        return str(p.resolve())


class NewsScoutConfig(BaseModel):
    search_queries: list[str] = ["AI news today", "tech industry news"]
    max_articles: int = 10


class ResearchConfig(BaseModel):
    max_topics_per_run: int = 3
    search_depth: int = 5


class TaskManagerConfig(BaseModel):
    reminder_days_ahead: int = 2
    max_todos_in_briefing: int = 10


class ContentStrategistConfig(BaseModel):
    ideas_per_run: int = 5
    platforms: list[str] = ["blog", "twitter", "youtube"]


class TrendForecasterConfig(BaseModel):
    forecast_weeks_ahead: int = 4
    max_searches: int = 5


class MemoryKeeperConfig(BaseModel):
    lookback_days: int = 7


class AgentsConfig(BaseModel):
    topics_of_interest: list[str] = ["artificial intelligence", "technology trends"]
    news_scout: NewsScoutConfig = NewsScoutConfig()
    research_assistant: ResearchConfig = ResearchConfig()
    task_manager: TaskManagerConfig = TaskManagerConfig()
    content_strategist: ContentStrategistConfig = ContentStrategistConfig()
    trend_forecaster: TrendForecasterConfig = TrendForecasterConfig()
    memory_keeper: MemoryKeeperConfig = MemoryKeeperConfig()


class ScheduleConfig(BaseModel):
    overnight_run_time: str = "02:00"
    timezone: str = "America/New_York"
    midday_todo_reminder: bool = True
    midday_run_time: str = "12:00"


class SafetyConfig(BaseModel):
    max_iterations_per_agent: int = 15
    agent_timeout_seconds: int = 300
    max_tokens_per_run: int = 500_000
    max_file_size_chars: int = 50_000
    vault_write_allowed_subdir: str = "AI-Agents"
    secret_patterns: list[str] = ["sk-ant-", "Bearer ", "api_key=", "API_KEY="]
    guardian_enabled: bool = True
    guardian_model: str = "claude-sonnet-4-6"


class IntegrationItem(BaseModel):
    enabled: bool = False
    base_url: str = ""
    timeout_seconds: int = 30


class IntegrationsConfig(BaseModel):
    openclaw: IntegrationItem = IntegrationItem()
    antigravity: IntegrationItem = IntegrationItem()


class Config(BaseModel):
    obsidian: ObsidianConfig
    agents: AgentsConfig = AgentsConfig()
    schedule: ScheduleConfig = ScheduleConfig()
    safety: SafetyConfig = SafetyConfig()
    integrations: IntegrationsConfig = IntegrationsConfig()
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    @model_validator(mode="after")
    def load_env_overrides(self) -> "Config":
        if not self.anthropic_api_key:
            self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        model_override = os.environ.get("ANTHROPIC_MODEL")
        if model_override:
            self.anthropic_model = model_override
        return self


_config: Optional[Config] = None


def load_config(config_path: str = "config.yaml") -> Config:
    global _config
    if _config is not None:
        return _config
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"config.yaml not found at {path.resolve()}")
    with open(path) as f:
        raw = yaml.safe_load(f)
    _config = Config(**raw)
    return _config


def get_config() -> Config:
    if _config is None:
        return load_config()
    return _config
