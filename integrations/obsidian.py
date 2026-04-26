import os
from datetime import date
from pathlib import Path
from loguru import logger
from utils.config import get_config


class PathEscapeError(Exception):
    pass


class ObsidianWriter:
    def __init__(self) -> None:
        cfg = get_config()
        self.vault_root = Path(cfg.obsidian.vault_path)
        self.agent_folder = cfg.obsidian.agent_folder
        self.allowed_root = (self.vault_root / self.agent_folder).resolve()

    def _resolve_safe(self, relative_path: str) -> Path:
        target = (self.allowed_root / relative_path).resolve()
        if not str(target).startswith(str(self.allowed_root)):
            raise PathEscapeError(
                f"Write path escapes allowed directory: {target} not under {self.allowed_root}"
            )
        return target

    def write(self, relative_path: str, content: str) -> str:
        path = self._resolve_safe(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)
        logger.info(f"Obsidian write: {path.relative_to(self.vault_root)}")
        return str(path)

    def read(self, relative_path: str) -> str:
        path = self._resolve_safe(relative_path)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def append(self, relative_path: str, content: str) -> str:
        path = self._resolve_safe(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        logger.debug(f"Obsidian append: {path.relative_to(self.vault_root)}")
        return str(path)

    def list_notes(self, subfolder: str = "") -> list[str]:
        base = (self.allowed_root / subfolder).resolve() if subfolder else self.allowed_root
        if not base.exists():
            return []
        return sorted([
            str(p.relative_to(self.allowed_root))
            for p in base.rglob("*.md")
        ])

    def resolve_wikilink(self, title: str) -> bool:
        for p in self.allowed_root.rglob("*.md"):
            if p.stem == title:
                return True
        return False

    def tier_folder(self, tier: str) -> str:
        return tier.capitalize()

    def dated_path(self, tier: str, note_title: str, run_date: date | None = None) -> str:
        d = run_date or date.today()
        folder = self.tier_folder(tier)
        return f"{folder}/{d.isoformat()} {note_title}.md"


_writer: ObsidianWriter | None = None


def get_writer() -> ObsidianWriter:
    global _writer
    if _writer is None:
        _writer = ObsidianWriter()
    return _writer
