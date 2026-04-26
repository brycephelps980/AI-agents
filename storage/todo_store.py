import json
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from loguru import logger

TODO_FILE = Path("data/todos.json")


def _read() -> list[dict]:
    if not TODO_FILE.exists():
        return []
    try:
        return json.loads(TODO_FILE.read_text())
    except Exception:
        return []


def _write(todos: list[dict]) -> None:
    TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = TODO_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(todos, indent=2, default=str))
    tmp.replace(TODO_FILE)


def get_all() -> list[dict]:
    return _read()


def get_open() -> list[dict]:
    return [t for t in _read() if t.get("status") != "done"]


def get_by_id(todo_id: str) -> Optional[dict]:
    return next((t for t in _read() if t["id"] == todo_id), None)


def add(title: str, description: str = "", priority: str = "medium",
        due_date: Optional[str] = None, tags: Optional[list[str]] = None) -> dict:
    todos = _read()
    todo = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "priority": priority,
        "due_date": due_date,
        "status": "open",
        "tags": tags or [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    todos.append(todo)
    _write(todos)
    logger.debug(f"Todo added: {title!r} [{priority}]")
    return todo


def update(todo_id: str, **fields) -> Optional[dict]:
    todos = _read()
    for todo in todos:
        if todo["id"] == todo_id:
            fields.pop("id", None)
            todo.update(fields)
            todo["updated_at"] = datetime.utcnow().isoformat()
            _write(todos)
            return todo
    logger.warning(f"Todo not found for update: {todo_id}")
    return None


def complete(todo_id: str) -> Optional[dict]:
    return update(todo_id, status="done")


def delete(todo_id: str) -> bool:
    todos = _read()
    filtered = [t for t in todos if t["id"] != todo_id]
    if len(filtered) == len(todos):
        return False
    _write(filtered)
    return True
