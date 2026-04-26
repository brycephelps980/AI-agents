"""
BaseAgent — shared foundation for all agents.
Provides: agentic tool-use loop, prompt caching, per-agent timeout,
token budget tracking, and retry-wrapped API calls.
"""
from __future__ import annotations

import json
import signal
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import anthropic
from loguru import logger

from utils.config import get_config
from utils.retry import retry_on_api_error
from utils.safety import redact_secrets


class AgentTimeoutError(Exception):
    pass


class MaxIterationsError(Exception):
    pass


class TokenBudgetExceededError(Exception):
    pass


class BaseAgent(ABC):
    name: str = "base"
    tier: str = "base"
    SYSTEM_PROMPT: str = "You are a helpful AI agent."

    def __init__(self) -> None:
        cfg = get_config()
        self.client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
        self.model = cfg.anthropic_model
        self.safety_cfg = cfg.safety
        self._tokens_used: int = 0

    # ── Prompt caching ────────────────────────────────────────────────────────

    def _get_cached_system(self) -> list[dict]:
        return [
            {
                "type": "text",
                "text": self.SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ]

    # ── Tool dispatch ─────────────────────────────────────────────────────────

    def _dispatch_tool(self, tool_name: str, tool_input: dict, registry: dict) -> Any:
        fn = registry.get(tool_name)
        if fn is None:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            result = fn(**tool_input)
            return result
        except Exception as e:
            logger.warning(f"Tool {tool_name} raised: {e}")
            return {"error": str(e)}

    def _build_tool_results(self, content_blocks: list, registry: dict) -> list[dict]:
        results = []
        for block in content_blocks:
            if block.type == "tool_use":
                logger.debug(f"[{self.name}] tool_use: {block.name}({json.dumps(block.input)[:120]})")
                raw = self._dispatch_tool(block.name, block.input, registry)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(raw, default=str),
                })
        return results

    # ── API call (retry-wrapped) ───────────────────────────────────────────────

    @retry_on_api_error
    def _call_api(self, messages: list[dict], tools: list[dict]) -> anthropic.types.Message:
        # Mark last tool with cache_control for tool schema caching
        cached_tools = list(tools)
        if cached_tools:
            last = dict(cached_tools[-1])
            last["cache_control"] = {"type": "ephemeral"}
            cached_tools[-1] = last

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self._get_cached_system(),
            messages=messages,
            tools=cached_tools,
        )
        usage = response.usage
        self._tokens_used += usage.input_tokens + usage.output_tokens
        if self._tokens_used > self.safety_cfg.max_tokens_per_run:
            raise TokenBudgetExceededError(
                f"Token budget exceeded: {self._tokens_used} > {self.safety_cfg.max_tokens_per_run}"
            )
        return response

    # ── Agentic loop ──────────────────────────────────────────────────────────

    def _run_agentic_loop(
        self,
        initial_messages: list[dict],
        tools: list[dict],
        tool_registry: dict,
        max_iterations: int | None = None,
    ) -> str:
        max_iter = max_iterations or self.safety_cfg.max_iterations_per_agent
        messages = list(initial_messages)

        for i in range(max_iter):
            response = self._call_api(messages, tools)

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        return redact_secrets(block.text)
                return ""

            if response.stop_reason == "tool_use":
                tool_results = self._build_tool_results(response.content, tool_registry)
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                continue

            logger.warning(f"[{self.name}] unexpected stop_reason: {response.stop_reason}")
            break

        raise MaxIterationsError(
            f"Agent '{self.name}' hit max iterations ({max_iter})"
        )

    # ── Timeout wrapper ───────────────────────────────────────────────────────

    def _timeout_handler(self, signum, frame):
        raise AgentTimeoutError(f"Agent '{self.name}' timed out after {self.safety_cfg.agent_timeout_seconds}s")

    def run_with_timeout(self, context: "RunContext") -> "AgentResult":
        from orchestrator.run_context import AgentResult
        signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.safety_cfg.agent_timeout_seconds)
        start = time.monotonic()
        try:
            result = self.run(context)
            return result
        except (AgentTimeoutError, MaxIterationsError, TokenBudgetExceededError) as e:
            elapsed = time.monotonic() - start
            logger.error(f"[{self.name}] safety abort after {elapsed:.1f}s: {e}")
            return AgentResult(
                agent_name=self.name,
                tier=self.tier,
                run_at=datetime.utcnow(),
                summary=f"Agent aborted: {e}",
                outputs=[],
                obsidian_files=[],
                errors=[str(e)],
            )
        except Exception as e:
            elapsed = time.monotonic() - start
            logger.error(f"[{self.name}] unexpected error after {elapsed:.1f}s: {e}")
            return AgentResult(
                agent_name=self.name,
                tier=self.tier,
                run_at=datetime.utcnow(),
                summary=f"Agent failed: {e}",
                outputs=[],
                obsidian_files=[],
                errors=[str(e)],
            )
        finally:
            signal.alarm(0)

    @abstractmethod
    def run(self, context: "RunContext") -> "AgentResult":
        """Execute the agent and return a structured result."""
        ...
