import json
from datetime import datetime
from pathlib import Path
from loguru import logger

STATE_FILE = Path("data/state.json")


def _read() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def _write(data: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    tmp.replace(STATE_FILE)


def get_last_run() -> datetime | None:
    data = _read()
    ts = data.get("last_full_run")
    if ts:
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            return None
    return None


def set_last_run(run_id: str) -> None:
    data = _read()
    data["last_full_run"] = datetime.utcnow().isoformat()
    data["last_run_id"] = run_id
    _write(data)
    logger.debug(f"State: last_full_run updated (run_id={run_id})")


def set_agent_last_run(agent_name: str) -> None:
    data = _read()
    agent_runs = data.setdefault("agent_last_run", {})
    agent_runs[agent_name] = datetime.utcnow().isoformat()
    _write(data)


def get_agent_last_run(agent_name: str) -> datetime | None:
    data = _read()
    ts = data.get("agent_last_run", {}).get(agent_name)
    if ts:
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            return None
    return None
