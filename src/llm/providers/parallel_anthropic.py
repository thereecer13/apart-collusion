"""
Parallel client for the Anthropic API (added 2026-10-28 for follow-up E1 with Claude agents;
see SPRINT_LOG.md). Same interface as AsyncOpenRouterParallelClient: execute_parallel(requests)
returns {custom_id: response}, where response is the parsed JSON answer or {"content": text}.

Used only with `run_endogenous.py --anthropic-direct`; every other run is unchanged.
- The key is read from ANTHROPIC_API_KEY.
- Claude 5.x models reject non-default sampling parameters, so `temperature` and `seed` in the
  request are ignored. Thinking stays at the model's defaults (adaptive, default effort).
- `max_tokens` is raised to MAX_TOKENS because thinking counts toward it.
- Token usage is summed in `self.usage` for cost accounting; the thinking text, if any, is kept
  in the response as "_thinking" (it reaches the request dumps only).
"""

import asyncio
import json
from typing import Any, Dict, List

import anthropic

MAX_TOKENS = 16000


class AnthropicLLM:
    """Stands in for llm_client: the runner reads only .model, .temperature and the flag below."""

    supports_structured_output = False   # JSON is requested in the prompt text, as for Claude via OpenRouter

    def __init__(self, model: str, temperature: float = 1.0):
        self.model = model
        self.temperature = temperature


class AnthropicParallelClient:

    def __init__(self, max_concurrent: int = 20, timeout: float = 600, max_retries: int = 6):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.max_retries = max_retries
        self.usage = {"requests": 0, "input_tokens": 0, "output_tokens": 0,
                      "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "errors": 0}

    def execute_parallel(self, requests_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        return asyncio.run(self._run(requests_list))

    async def _run(self, requests_list):
        client = anthropic.AsyncAnthropic(max_retries=self.max_retries, timeout=self.timeout)
        sem = asyncio.Semaphore(self.max_concurrent)
        try:
            pairs = await asyncio.gather(*[self._one(client, sem, r) for r in requests_list])
        finally:
            await client.close()
        return dict(pairs)

    async def _one(self, client, sem, request):
        cid = request["custom_id"]
        system = "\n\n".join(m["content"] for m in request["messages"] if m["role"] == "system")
        messages = [m for m in request["messages"] if m["role"] != "system"]
        async with sem:
            try:
                resp = await client.messages.create(
                    model=request["model"].split("/")[-1], max_tokens=MAX_TOKENS,
                    system=system, messages=messages,
                )
            except anthropic.APIError as e:
                self.usage["errors"] += 1
                print(f"Error in request {cid}: {e}")
                return cid, {"status": "error", "error": str(e)}
        u = resp.usage
        self.usage["requests"] += 1
        for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
            self.usage[k] += getattr(u, k, 0) or 0
        text = "".join(b.text for b in resp.content if b.type == "text")
        thinking = "".join(getattr(b, "thinking", "") or "" for b in resp.content if b.type == "thinking")
        try:
            parsed = json.loads(text)
            out = parsed if isinstance(parsed, dict) else {"content": text}
        except (json.JSONDecodeError, ValueError):
            out = {"status": "success", "content": text}
        if resp.stop_reason == "max_tokens":
            out["_truncated"] = True
        if thinking:
            out["_thinking"] = thinking
        return cid, out
