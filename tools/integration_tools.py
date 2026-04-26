from loguru import logger


def openclaw_action(action: str, params: dict) -> dict:
    from integrations.openclaw import get_client, IntegrationNotConfigured
    try:
        return get_client().dispatch(action, params)
    except IntegrationNotConfigured as e:
        logger.warning(str(e))
        return {"error": str(e)}


def antigravity_action(action: str, params: dict) -> dict:
    from integrations.antigravity import get_client, IntegrationNotConfigured
    try:
        return get_client().dispatch(action, params)
    except IntegrationNotConfigured as e:
        logger.warning(str(e))
        return {"error": str(e)}


OPENCLAW_TOOL = {
    "name": "openclaw_action",
    "description": (
        "Send an action to the OpenClaw integration. "
        "Only available when OpenClaw is enabled in config.yaml."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "description": "The action name to perform"},
            "params": {"type": "object", "description": "Parameters for the action", "default": {}},
        },
        "required": ["action"],
    },
}

ANTIGRAVITY_TOOL = {
    "name": "antigravity_action",
    "description": (
        "Send an action to the AntiGravity integration. "
        "Only available when AntiGravity is enabled in config.yaml."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "description": "The action name to perform"},
            "params": {"type": "object", "description": "Parameters for the action", "default": {}},
        },
        "required": ["action"],
    },
}

TOOL_REGISTRY = {
    "openclaw_action": openclaw_action,
    "antigravity_action": antigravity_action,
}
