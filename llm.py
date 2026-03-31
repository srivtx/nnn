"""
LLM client — thin wrapper around the OpenAI SDK pointed at a local server.
Handles the tool-calling loop automatically.

SPEED OPTIMIZATIONS:
  1. Response caching (LRU) — skip the LLM entirely for repeated prompts
  2. Streaming — start processing tokens immediately, don't wait for full response
  3. Parallel tool execution — run independent tool calls concurrently
  4. Adaptive max_tokens — use smaller limits for lightweight calls
  5. Connection keep-alive — reuse TCP connections to the LM server
  6. KV cache prefix sharing — all agents share a common system-prompt prefix
     so LM Studio can reuse its GPU KV cache across agent switches
"""

import re
import json
import hashlib
import threading
from types import SimpleNamespace
from collections import OrderedDict
from contextlib import nullcontext
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from rich.console import Console
import config

console = Console()

client = OpenAI(
    base_url=config.LM_BASE_URL,
    api_key=config.LM_API_KEY,
    timeout=config.HTTP_TIMEOUT,
    max_retries=1,
)


# ── Response Cache (thread-safe LRU) ─────────────────────
class _LRUCache:
    """Simple thread-safe LRU cache for LLM responses."""
    def __init__(self, maxsize: int):
        self._cache: OrderedDict[str, str] = OrderedDict()
        self._maxsize = maxsize
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def _key(self, messages: list[dict], tools: list[dict] | None) -> str:
        raw = json.dumps(messages, sort_keys=True) + json.dumps(tools or [], sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, messages, tools) -> str | None:
        if not config.ENABLE_CACHE:
            return None
        k = self._key(messages, tools)
        with self._lock:
            if k in self._cache:
                self._cache.move_to_end(k)
                self.hits += 1
                return self._cache[k]
            self.misses += 1
            return None

    def put(self, messages, tools, value: str):
        if not config.ENABLE_CACHE:
            return
        k = self._key(messages, tools)
        with self._lock:
            self._cache[k] = value
            self._cache.move_to_end(k)
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

_cache = _LRUCache(config.CACHE_MAX_SIZE)


def _detect_model() -> str:
    """Auto-detect the first available model from the server."""
    if config.LM_MODEL:
        return config.LM_MODEL
    try:
        models = client.models.list()
        model_id = models.data[0].id if models.data else "local-model"
        return model_id
    except Exception:
        return "local-model"


_model = None

def get_model() -> str:
    global _model
    if _model is None:
        _model = _detect_model()
    return _model


def chat(
    messages: list[dict],
    tools: list[dict] | None = None,
    tool_functions: dict | None = None,
    agent_name: str = "Agent",
    max_tokens: int | None = None,
    temperature: float | None = None,
    stream: bool = True,
) -> str:
    """
    Send messages to the LLM. If the LLM responds with tool calls,
    execute them and continue the conversation until we get a final text response.

    Args:
        messages: The conversation so far (list of role/content dicts).
        tools: OpenAI-format tool schemas (optional).
        tool_functions: Map of tool name → callable (optional).
        agent_name: For logging purposes.
        max_tokens: Override token limit for this call (default: config.MAX_TOKENS).
        temperature: Override temperature for this call (default: config.TEMPERATURE).
        stream: Whether to print tokens live (default: True). Set False for internal calls.

    Returns:
        The final text response from the LLM.
    """
    # ── Cache check (only for calls with no tools — deterministic) ──
    if not tools:
        cached = _cache.get(messages, tools)
        if cached is not None:
            console.print(f"  [dim]cached[/dim] {agent_name}")
            return cached

    model = get_model()
    tool_functions = tool_functions or {}
    effective_max_tokens = max_tokens or config.MAX_TOKENS
    effective_temp = temperature if temperature is not None else config.TEMPERATURE
    max_iterations = 15  # safety cap on tool-call loops
    consecutive_errors = 0  # detect stuck loops
    duplicate_count = 0     # detect exact same call repeated
    last_tool_call = None   # (name, args) — detect duplicate calls

    for iteration in range(max_iterations):
        # ── Trim context if messages are getting too long ──
        total_chars = sum(len(m.get("content", "") or "") for m in messages)
        if total_chars > 16000 and len(messages) > 6:
            # Keep system prompt + last 6 messages to stay within context window
            messages = [messages[0]] + messages[-6:]

        kwargs = dict(
            model=model,
            messages=messages,
            temperature=effective_temp,
            max_tokens=effective_max_tokens,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        # Qwen3 thinking mode wastes huge amounts of tokens — disable it
        if config.DISABLE_THINKING:
            kwargs["extra_body"] = {
                "chat_template_kwargs": {"enable_thinking": False}
            }

        # ── Get LLM response (streaming or blocking) ──
        is_main = threading.current_thread() is threading.main_thread()
        if config.ENABLE_STREAMING and stream and is_main:
            if not tools:
                # Text-only: stream directly to console
                result = _stream_response(kwargs, agent_name)
                _cache.put(messages, tools, result)
                return _strip_think(result)

            # Tool calls: stream with progress counter
            msg_content, tool_calls = _stream_with_tools(kwargs, agent_name)
            if tool_calls is None:
                # Pure text response (no tool calls)
                return msg_content
        else:
            # Non-streaming fallback (threads / streaming disabled)
            spinner = console.status("[dim]thinking...[/dim]", spinner="dots") if is_main else nullcontext()
            for attempt in range(2):
                with spinner:
                    try:
                        response = client.chat.completions.create(**kwargs)
                        break
                    except Exception as e:
                        if attempt == 0 and "timeout" in str(e).lower():
                            console.print(f"    [dim]timeout, retrying...[/dim]")
                            continue
                        console.print(f"  [red]llm error:[/red] {e}")
                        return f"Error communicating with LLM: {e}"

            choice = response.choices[0]
            message = choice.message

            if not message.tool_calls:
                result = _strip_think(message.content or "")
                if not tools:
                    _cache.put(messages, tools, result)
                return result

            msg_content = _strip_think(message.content or "")
            tool_calls = message.tool_calls

        # ── Execute tool calls (in PARALLEL if multiple) ──
        messages.append({
            "role": "assistant",
            "content": msg_content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in tool_calls
            ],
        })

        if len(tool_calls) == 1:
            # Single tool call — run inline (no thread overhead)
            tc = tool_calls[0]
            result = _exec_tool(tc, tool_functions, agent_name)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": str(result),
            })
            # Detect duplicate calls (same tool + same args = stuck)
            call_sig = (tc.function.name, tc.function.arguments)
            if call_sig == last_tool_call:
                duplicate_count += 1
                if duplicate_count >= 2:
                    console.print("    [dim]stuck in loop (repeat call), moving on[/dim]")
                    return result
                consecutive_errors += 1
            else:
                duplicate_count = 0
            last_tool_call = call_sig

            # Detect stuck error loops (e.g. edit_file failing, wrong runtime)
            result_lower = str(result).lower()
            ERROR_SIGNALS = [
                "error", "exit code:", "stderr", "traceback",
                "refused", "timed out", "can't open", "no such file",
                "command not found", "permission denied", "syntax error",
            ]
            if any(sig in result_lower for sig in ERROR_SIGNALS):
                consecutive_errors += 1
                if consecutive_errors >= 2:
                    console.print("    [dim]stuck in error loop, moving on[/dim]")
                    return result
            else:
                consecutive_errors = 0
        else:
            # PARALLEL tool execution — all independent calls run at once
            console.print(f"    [dim]{len(tool_calls)} tools in parallel[/dim]")
            results = {}
            with ThreadPoolExecutor(max_workers=len(tool_calls)) as pool:
                futures = {
                    pool.submit(_exec_tool, tc, tool_functions, agent_name): tc
                    for tc in tool_calls
                }
                for future in as_completed(futures):
                    tc = futures[future]
                    results[tc.id] = future.result()

            # Append results in original order (important for the LLM)
            all_errors = True
            for tc in tool_calls:
                r = str(results[tc.id])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": r,
                })
                r_lower = r.lower()
                if not ("error" in r_lower or "exit code:" in r_lower
                        or "stderr" in r_lower or "traceback" in r_lower):
                    all_errors = False

            # Track error loops for parallel calls too
            if all_errors:
                consecutive_errors += 1
                if consecutive_errors >= 3:
                    console.print("    [dim]stuck in error loop, moving on[/dim]")
                    return str(results[tool_calls[-1].id])
            else:
                consecutive_errors = 0

    return "Max tool iterations reached."


def _fix_code_escapes(fn_args: dict) -> dict:
    """Fix double-escaped newlines from small models.

    Small LLMs sometimes send \\\\n in JSON where they mean \\n,
    resulting in literal \\n characters in code instead of real newlines.
    """
    _CODE_PARAMS = {"content", "code", "new_code", "old_code"}
    for key in _CODE_PARAMS & fn_args.keys():
        val = fn_args[key]
        if not isinstance(val, str) or '\\n' not in val:
            continue
        if '\n' not in val:
            # Entire content uses literal \n — all are double-escaped
            fn_args[key] = val.replace('\\n', '\n')
        else:
            # Mix of real and literal — only fix obvious cases:
            # literal \n followed by whitespace (indentation after line break)
            fn_args[key] = re.sub(r'\\n([ \t])', '\n\\1', val)
    return fn_args


def _exec_tool(tc, tool_functions: dict, agent_name: str) -> str:
    """Execute a single tool call. Used by both serial and parallel paths."""
    fn_name = tc.function.name
    try:
        fn_args = json.loads(tc.function.arguments)
        fn_args = _fix_code_escapes(fn_args)
    except json.JSONDecodeError:
        console.print(f"    [dim]→ bad JSON args, skipping[/dim]")
        return f"Tool error: could not parse arguments as JSON. Send valid JSON."

    # Format args as clean key=value instead of raw dict
    arg_str = " ".join(f"{k}={_truncate(str(v), 30)}" for k, v in fn_args.items()) if fn_args else ""
    console.print(
        f"    [cyan]{fn_name}[/cyan] [dim]{arg_str}[/dim]"
    )

    if fn_name in tool_functions:
        try:
            result = tool_functions[fn_name](**fn_args)
        except Exception as e:
            result = f"Tool error: {e}"
    else:
        result = f"Unknown tool: {fn_name}"

    # Cap tool output to prevent blowing the context window
    # read_file gets a higher cap so the model can see enough lines for edit_lines
    result = str(result)
    cap = 6000 if fn_name == "read_file" else 2000
    if len(result) > cap:
        result = result[:cap] + "\n... (truncated to save context)"

    # Show a 1-line summary of result, not raw content
    first_line = str(result).split('\n')[0].strip()
    console.print(f"    [dim]→ {_truncate(first_line, 80)}[/dim]")
    return result


def _strip_think(text: str) -> str:
    """Remove <think>...</think> blocks that Qwen3 models emit."""
    return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()


def _stream_with_tools(kwargs: dict, agent_name: str):
    """Stream an LLM response that may include tool calls.

    Shows a character counter so the user sees progress instead of a
    frozen spinner.  Returns (content, tool_calls) where tool_calls is
    a list of SimpleNamespace objects or None.
    """
    kwargs_copy = {**kwargs, "stream": True}

    try:
        stream_iter = client.chat.completions.create(**kwargs_copy)
    except Exception as e:
        console.print(f"  [red]stream error:[/red] {e}")
        # Fallback to blocking
        try:
            response = client.chat.completions.create(**kwargs)
            msg = response.choices[0].message
            content = _strip_think(msg.content or "")
            return content, msg.tool_calls
        except Exception as e2:
            return f"Error: {e2}", None

    content_parts = []
    tc_acc = {}           # index → {"id", "name", "arguments"}
    total_arg_chars = 0
    last_report = 0

    for chunk in stream_iter:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta

        if delta.content:
            content_parts.append(delta.content)

        if hasattr(delta, "tool_calls") and delta.tool_calls:
            for tc_delta in delta.tool_calls:
                idx = tc_delta.index
                if idx not in tc_acc:
                    tc_acc[idx] = {"id": "", "name": "", "arguments": ""}
                if tc_delta.id:
                    tc_acc[idx]["id"] = tc_delta.id
                if tc_delta.function:
                    if tc_delta.function.name:
                        tc_acc[idx]["name"] += tc_delta.function.name
                    if tc_delta.function.arguments:
                        tc_acc[idx]["arguments"] += tc_delta.function.arguments
                        total_arg_chars += len(tc_delta.function.arguments)

            # Progress indicator every ~500 chars
            if total_arg_chars - last_report >= 500:
                last_report = total_arg_chars
                print(
                    f"\r    [generating... {total_arg_chars:,} chars]  ",
                    end="", flush=True,
                )

    # Clear progress line
    if last_report > 0:
        print("\r" + " " * 50 + "\r", end="", flush=True)

    content = _strip_think("".join(content_parts))

    if not tc_acc:
        return content, None

    tool_calls = []
    for idx in sorted(tc_acc.keys()):
        tc = tc_acc[idx]
        tool_calls.append(SimpleNamespace(
            id=tc["id"],
            function=SimpleNamespace(
                name=tc["name"],
                arguments=tc["arguments"],
            ),
        ))

    return content, tool_calls


def _stream_response(kwargs: dict, agent_name: str) -> str:
    """Stream a response from the LLM, printing tokens as they arrive."""
    try:
        kwargs["stream"] = True
        stream = client.chat.completions.create(**kwargs)
        chunks = []
        started = False
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                if not started:
                    console.print("", end="")  # ensure clean line
                    started = True
                console.print(delta.content, end="", highlight=False)
                chunks.append(delta.content)
        if started:
            console.print()  # final newline
        return "".join(chunks)
    except Exception as e:
        console.print(f"  [red]stream error:[/red] {e}")
        # Fallback to non-streaming
        kwargs.pop("stream", None)
        try:
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as e2:
            return f"Error communicating with LLM: {e2}"


def get_cache_stats() -> dict:
    """Return cache hit/miss stats for diagnostics."""
    return {"hits": _cache.hits, "misses": _cache.misses}


def _truncate(text: str, length: int = 120) -> str:
    return text[:length] + "…" if len(text) > length else text
