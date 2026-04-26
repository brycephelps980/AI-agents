"""
Staged file tools — agent writes are buffered in RunContext.staged_outputs.
Nothing touches disk until SafetyGuardianAgent approves them.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from orchestrator.run_context import RunContext

_active_context: "RunContext | None" = None


def set_active_context(ctx: "RunContext") -> None:
    global _active_context
    _active_context = ctx


def clear_active_context() -> None:
    global _active_context
    _active_context = None


def stage_write(relative_path: str, content: str) -> str:
    if _active_context is None:
        raise RuntimeError("No active RunContext — call set_active_context() first")
    _active_context.stage_output(relative_path, content)
    logger.debug(f"Staged write: {relative_path}")
    return f"Staged for safety review: {relative_path}"


def obsidian_read(relative_path: str) -> str:
    from integrations.obsidian import get_writer
    content = get_writer().read(relative_path)
    logger.debug(f"Obsidian read: {relative_path} ({len(content)} chars)")
    return content if content else "(file not found or empty)"


def obsidian_list_notes(subfolder: str = "") -> list[str]:
    from integrations.obsidian import get_writer
    notes = get_writer().list_notes(subfolder)
    logger.debug(f"Obsidian list_notes: {subfolder!r} → {len(notes)} notes")
    return notes


STAGE_WRITE_TOOL = {
    "name": "stage_write",
    "description": (
        "Stage a markdown file to be written to the Obsidian vault. "
        "The file is queued for safety review and written to disk only after approval. "
        "Path is relative to the AI-Agents folder in the vault."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "relative_path": {
                "type": "string",
                "description": "Vault-relative path, e.g. 'Present/2026-04-26 News Scout.md'",
            },
            "content": {
                "type": "string",
                "description": "Full markdown content of the note including YAML frontmatter.",
            },
        },
        "required": ["relative_path", "content"],
    },
}

OBSIDIAN_READ_TOOL = {
    "name": "obsidian_read",
    "description": "Read the contents of an existing Obsidian note. Returns empty string if not found.",
    "input_schema": {
        "type": "object",
        "properties": {
            "relative_path": {
                "type": "string",
                "description": "Vault-relative path to the note, e.g. 'Past/2026-04-19 Memory Summary.md'",
            },
        },
        "required": ["relative_path"],
    },
}

OBSIDIAN_LIST_TOOL = {
    "name": "obsidian_list_notes",
    "description": "List all existing markdown notes in a vault subfolder. Returns a list of relative paths.",
    "input_schema": {
        "type": "object",
        "properties": {
            "subfolder": {
                "type": "string",
                "description": "Subfolder to list notes in (e.g. 'Past', 'Present'). Leave empty for all.",
                "default": "",
            },
        },
        "required": [],
    },
}

TOOL_REGISTRY = {
    "stage_write": stage_write,
    "obsidian_read": obsidian_read,
    "obsidian_list_notes": obsidian_list_notes,
}
