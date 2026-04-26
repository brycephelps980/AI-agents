import storage.todo_store as store
from loguru import logger


def todo_read() -> list[dict]:
    todos = store.get_open()
    logger.debug(f"todo_read: {len(todos)} open todos")
    return todos


def todo_write(title: str, description: str = "", priority: str = "medium",
               due_date: str = "", tags: list[str] | None = None) -> dict:
    todo = store.add(title, description, priority, due_date or None, tags)
    logger.info(f"todo_write: created '{title}' [{priority}]")
    return todo


def todo_complete(todo_id: str) -> dict:
    result = store.complete(todo_id)
    if result:
        logger.info(f"todo_complete: marked done ({todo_id})")
        return result
    return {"error": f"Todo not found: {todo_id}"}


def todo_update(todo_id: str, title: str = "", description: str = "",
                priority: str = "", status: str = "", due_date: str = "") -> dict:
    fields = {}
    if title:
        fields["title"] = title
    if description:
        fields["description"] = description
    if priority:
        fields["priority"] = priority
    if status:
        fields["status"] = status
    if due_date:
        fields["due_date"] = due_date
    result = store.update(todo_id, **fields)
    return result or {"error": f"Todo not found: {todo_id}"}


TODO_READ_TOOL = {
    "name": "todo_read",
    "description": "Read all open (not completed) to-do items. Returns a list of todo objects.",
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

TODO_WRITE_TOOL = {
    "name": "todo_write",
    "description": "Create a new to-do item.",
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Short title for the task"},
            "description": {"type": "string", "description": "Details about the task", "default": ""},
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high", "critical"],
                "description": "Priority level",
                "default": "medium",
            },
            "due_date": {"type": "string", "description": "ISO date string (YYYY-MM-DD), optional", "default": ""},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags", "default": []},
        },
        "required": ["title"],
    },
}

TODO_COMPLETE_TOOL = {
    "name": "todo_complete",
    "description": "Mark a to-do item as done by its ID.",
    "input_schema": {
        "type": "object",
        "properties": {
            "todo_id": {"type": "string", "description": "UUID of the todo item"},
        },
        "required": ["todo_id"],
    },
}

TODO_UPDATE_TOOL = {
    "name": "todo_update",
    "description": "Update fields on an existing to-do item by ID. Only provided fields are changed.",
    "input_schema": {
        "type": "object",
        "properties": {
            "todo_id": {"type": "string", "description": "UUID of the todo item"},
            "title": {"type": "string", "default": ""},
            "description": {"type": "string", "default": ""},
            "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"], "default": ""},
            "status": {"type": "string", "enum": ["open", "in_progress", "done"], "default": ""},
            "due_date": {"type": "string", "default": ""},
        },
        "required": ["todo_id"],
    },
}

TOOL_REGISTRY = {
    "todo_read": todo_read,
    "todo_write": todo_write,
    "todo_complete": todo_complete,
    "todo_update": todo_update,
}
