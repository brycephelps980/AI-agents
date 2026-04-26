import os
import httpx
from loguru import logger
from utils.config import get_config


class IntegrationNotConfigured(Exception):
    pass


class AntiGravityClient:
    """Adapter stub for AntiGravity integration. Fill in dispatch() when API credentials are available."""

    def __init__(self) -> None:
        cfg = get_config()
        self.enabled = cfg.integrations.antigravity.enabled
        self.base_url = cfg.integrations.antigravity.base_url
        self.timeout = cfg.integrations.antigravity.timeout_seconds
        self.api_key = os.environ.get("ANTIGRAVITY_API_KEY", "")

    def dispatch(self, action: str, params: dict) -> dict:
        if not self.enabled:
            raise IntegrationNotConfigured("AntiGravity integration is disabled. Set enabled: true in config.yaml.")
        logger.info(f"AntiGravity dispatch: action={action}, params={params}")
        # TODO: implement real API call once credentials are available
        # response = httpx.post(
        #     f"{self.base_url}/{action}",
        #     json=params,
        #     headers={"Authorization": f"Bearer {self.api_key}"},
        #     timeout=self.timeout,
        # )
        # response.raise_for_status()
        # return response.json()
        return {"status": "stub", "action": action, "params": params}


_client: AntiGravityClient | None = None


def get_client() -> AntiGravityClient:
    global _client
    if _client is None:
        _client = AntiGravityClient()
    return _client
