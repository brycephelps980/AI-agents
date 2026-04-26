from duckduckgo_search import DDGS
from loguru import logger


def web_search(query: str, max_results: int = 5) -> list[dict]:
    logger.debug(f"web_search: {query!r} (max={max_results})")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [{"title": r["title"], "url": r["href"], "snippet": r["body"]} for r in results]
    except Exception as e:
        logger.warning(f"web_search failed for {query!r}: {e}")
        return []


WEB_SEARCH_TOOL = {
    "name": "web_search",
    "description": (
        "Search the web using DuckDuckGo. Returns a list of results with title, URL, and snippet. "
        "Use this to find current news, research topics, or verify information."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string",
            },
            "max_results": {
                "type": "integer",
                "description": "Number of results to return (1–10). Default is 5.",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}

TOOL_REGISTRY = {"web_search": web_search}
