import time
from functools import wraps
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging
import anthropic


def retry_on_api_error(func):
    """Retry Anthropic API calls on transient errors with exponential backoff."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        attempts = 0
        max_attempts = 4
        wait = 2
        while attempts < max_attempts:
            try:
                return func(*args, **kwargs)
            except anthropic.RateLimitError as e:
                retry_after = getattr(e, "retry_after", wait)
                logger.warning(f"Rate limit hit — waiting {retry_after}s before retry {attempts + 1}/{max_attempts}")
                time.sleep(float(retry_after) if retry_after else wait)
            except (anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
                logger.warning(f"API connection error ({e}) — retry {attempts + 1}/{max_attempts} in {wait}s")
                time.sleep(wait)
            except anthropic.APIStatusError as e:
                if e.status_code >= 500:
                    logger.warning(f"API server error {e.status_code} — retry {attempts + 1}/{max_attempts} in {wait}s")
                    time.sleep(wait)
                else:
                    raise
            attempts += 1
            wait = min(wait * 2, 32)
        raise RuntimeError(f"API call failed after {max_attempts} attempts")
    return wrapper
