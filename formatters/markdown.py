from datetime import date


def build_frontmatter(fields: dict) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {str(value).lower()}")
        else:
            safe = str(value).replace('"', '\\"')
            lines.append(f'{key}: "{safe}"')
    lines.append("---")
    return "\n".join(lines)


def callout(kind: str, title: str, body: str) -> str:
    """Obsidian callout block, e.g. > [!info] Title"""
    header = f"> [!{kind}] {title}"
    indented = "\n".join(f"> {line}" for line in body.strip().splitlines())
    return f"{header}\n{indented}"


def wikilink(title: str) -> str:
    return f"[[{title}]]"


def h1(text: str) -> str:
    return f"# {text}"


def h2(text: str) -> str:
    return f"## {text}"


def h3(text: str) -> str:
    return f"### {text}"


def agent_note_header(title: str, run_date: date, tier: str, agent: str,
                      tags: list[str] | None = None) -> str:
    fm = build_frontmatter({
        "title": title,
        "date": run_date.isoformat(),
        "tier": tier,
        "agent": agent,
        "tags": (tags or []) + ["ai-agents", tier, agent],
        "created_by": "ai-agents-system",
    })
    return f"{fm}\n\n{h1(title)}\n"
