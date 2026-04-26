from datetime import date
from orchestrator.run_context import RunContext
from formatters.markdown import build_frontmatter, h1, h2, callout, wikilink


def build_daily_briefing(ctx: RunContext) -> str:
    d = ctx.run_date
    title = f"Daily Briefing — {d.strftime('%A, %B %-d %Y')}"
    elapsed = ctx.elapsed_seconds()

    all_agents = []
    all_errors: list[str] = []
    for tr in ctx.tier_results.values():
        for ar in tr.agents.values():
            all_agents.append(ar.agent_name)
            all_errors.extend(ar.errors)

    fm = build_frontmatter({
        "title": title,
        "date": d.isoformat(),
        "tags": ["daily-briefing", "ai-agents", "automated"],
        "run_id": ctx.run_id,
        "agents_run": all_agents,
        "created_by": "ai-agents-system",
    })

    sections: list[str] = [fm, "", h1(title), ""]
    sections.append(callout("info", "Auto-generated",
                             f"Generated at {d.isoformat()} by the AI Agents system · "
                             f"Run ID: `{ctx.run_id[:8]}`"))
    sections.append("")

    # Past tier
    past = ctx.tier_results.get("past")
    if past and past.tier_summary:
        sections.append(h2("Memory & Patterns"))
        sections.append(callout("note", "Past Tier", past.tier_summary))
        mem_path = f"Past/{d.isoformat()} Memory Summary"
        pat_path = f"Past/{d.isoformat()} Pattern Analysis"
        sections.append(f"\n- {wikilink(mem_path)}\n- {wikilink(pat_path)}\n")

    # Present tier
    present = ctx.tier_results.get("present")
    if present and present.tier_summary:
        sections.append(h2("Today's Intelligence"))
        sections.append(callout("note", "Present Tier", present.tier_summary))
        news_path = f"Present/{d.isoformat()} News Scout"
        sections.append(f"\n- {wikilink(news_path)}\n")

    # Future tier
    future = ctx.tier_results.get("future")
    if future and future.tier_summary:
        sections.append(h2("Forward Look"))
        sections.append(callout("tip", "Future Tier", future.tier_summary))
        trend_path = f"Future/{d.isoformat()} Trend Forecast"
        content_path = f"Future/{d.isoformat()} Content Calendar"
        sections.append(f"\n- {wikilink(trend_path)}\n- {wikilink(content_path)}\n")

    # Footer
    error_note = f" · {len(all_errors)} errors" if all_errors else ""
    prev_date = date.fromordinal(d.toordinal() - 1)
    prev_path = f"Daily Briefings/{prev_date.isoformat()} Daily Briefing"
    sections.append("---")
    sections.append(
        f"*Run completed in {elapsed / 60:.1f}m{error_note} · {wikilink(prev_path)}*"
    )

    return "\n".join(sections)
