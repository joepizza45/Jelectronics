"""Shared agent loop: web research with Claude, ending in a schema-checked submit tool call."""

from __future__ import annotations

import json
import logging
import os
from typing import TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

log = logging.getLogger(__name__)

MODEL = os.environ.get("JELECTRONICS_MODEL", "claude-opus-5-5")
MAX_CONTINUATIONS = 12

T = TypeVar("T", bound=BaseModel)

_client: anthropic.Anthropic | None = None


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def web_tools(search_uses: int, fetch_uses: int, domains: list[str] | None = None) -> list[dict]:
    tools: list[dict] = []
    if search_uses:
        search = {"type": "web_search_20260209", "name": "web_search", "max_uses": search_uses}
        tools.append(search)
    if fetch_uses:
        fetch = {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": fetch_uses}
        if domains:
            fetch["allowed_domains"] = domains
        tools.append(fetch)
    return tools


def run_agent(
    *,
    name: str,
    system: str,
    prompt: str,
    output: type[T],
    tools: list[dict],
    effort: str = "high",
) -> T:
    """Run one agent until it calls its submit tool with input that validates against `output`."""
    submit_name = f"submit_{name}"
    submit_tool = {
        "name": submit_name,
        "description": f"Submit your final {name} report. Call this exactly once, when your research is done.",
        "input_schema": output.model_json_schema(),
    }
    messages: list[dict] = [{"role": "user", "content": prompt}]

    for turn in range(MAX_CONTINUATIONS):
        with client().beta.messages.stream(
            model=MODEL,
            max_tokens=64000,
            system=system,
            messages=messages,
            tools=[*tools, submit_tool],
            thinking={"type": "adaptive"},
            output_config={"effort": effort},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            response = stream.get_final_message()

        log.info("[%s] turn %d stop_reason=%s usage=%s", name, turn, response.stop_reason, response.usage)

        if response.stop_reason == "refusal":
            raise RuntimeError(f"{name} agent request was declined: {response.stop_details}")

        if messages[-1]["role"] == "assistant":
            # Resuming after pause_turn: the response continues the same assistant turn.
            messages[-1]["content"] = [*messages[-1]["content"], *response.content]
        else:
            messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "pause_turn":
            # Server-side search loop hit its iteration cap; resend to resume.
            continue

        submit = next((b for b in response.content if b.type == "tool_use" and b.name == submit_name), None)
        if submit is None:
            if response.stop_reason == "max_tokens":
                nudge = "You ran out of output space. Stop researching and call " + submit_name + " now with what you have."
            else:
                nudge = f"Call {submit_name} now with your final results."
            messages.append({"role": "user", "content": nudge})
            continue

        try:
            return output.model_validate(submit.input)
        except ValidationError as e:
            log.warning("[%s] submit failed validation: %s", name, e)
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": submit.id,
                    "is_error": True,
                    "content": "Input did not match the schema, fix these errors and call again:\n" + str(e),
                }],
            })

    raise RuntimeError(f"{name} agent did not submit a valid report after {MAX_CONTINUATIONS} turns")


def as_json(model: BaseModel | list[BaseModel]) -> str:
    if isinstance(model, list):
        return json.dumps([m.model_dump() for m in model], indent=2)
    return model.model_dump_json(indent=2)
