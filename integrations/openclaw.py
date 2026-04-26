import os
import httpx
from loguru import logger
from utils.config import get_config


class IntegrationNotConfigured(Exception):
    pass


class OpenClawClient:
    """Adapter stub for OpenClaw integration. Fill in dispatch() when API credentials are available."""

    def __init__(self) -> None:
        cfg = get_config()
        self.enabled = cfg.integrations.openclaw.enabled
        self.base_url = cfg.integrations.openclaw.base_url
        self.timeout = cfg.integrations.openclaw.timeout_seconds
        self.api_key = os.environ.get("OPENCLAW_API_KEY", "")

    def dispatch(self, action: str, params: dict) -> dict:
        if not self.enabled:
            raise IntegrationNotConfigured("OpenClaw integration is disabled. Set enabled: true in config.yaml.")
        logger.info(f"OpenClaw dispatch: action={action}, params={params}")
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


_client: OpenClawClient | None = None


def get_client() -> OpenClawClient:
    global _client
    if _client is None:
        _client = OpenClawClient()
    return _client
