import re
from loguru import logger


_DEFAULT_SECRET_PATTERNS = [
    r"sk-ant-[A-Za-z0-9\-_]{10,}",
    r"Bearer [A-Za-z0-9\-_\.]{10,}",
    r"api[_-]?key\s*=\s*['\"][^'\"]{8,}['\"]",
    r"API[_-]?KEY\s*=\s*[A-Za-z0-9\-_]{8,}",
]


def redact_secrets(text: str, extra_patterns: list[str] | None = None) -> str:
    patterns = _DEFAULT_SECRET_PATTERNS + (extra_patterns or [])
    for pattern in patterns:
        text = re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)
    return text


def contains_secret(text: str, extra_patterns: list[str] | None = None) -> bool:
    patterns = _DEFAULT_SECRET_PATTERNS + (extra_patterns or [])
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def validate_output_size(content: str, max_chars: int) -> bool:
    if len(content) > max_chars:
        logger.warning(f"Output exceeds max size ({len(content)} > {max_chars} chars)")
        return False
    return True
