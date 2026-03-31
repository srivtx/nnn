"""
Configuration for the multi-agent system.
Points to your local LM Studio server.
"""

import os

# ── LM Server ──────────────────────────────────────────────
LM_BASE_URL = os.environ.get("LM_BASE_URL", "http://localhost:1234/v1")
LM_API_KEY = os.environ.get("LM_API_KEY", "lm-studio")  # placeholder, LM Studio doesn't need a real key
LM_MODEL = os.environ.get("LM_MODEL", "")  # empty = auto-detect from server

# ── Generation defaults ───────────────────────────────────
TEMPERATURE = 0.6
TEMPERATURE_CODE = 0.3       # low: 3B models need tight focus for tool use
MAX_TOKENS = 8192            # main generation cap

# ── Speed Optimizations ────────────────────────────────────
MAX_TOKENS_PLAN = 2048       # plan JSON + some breathing room
MAX_TOKENS_SUMMARY = 1024    # summaries
MAX_TOKENS_TOOL_AGENT = 8192 # agents writing code

# Parallel execution — run independent agents concurrently
PARALLEL_AGENTS = True        # set False to revert to sequential
MAX_PARALLEL_WORKERS = 3      # how many agents can run simultaneously

# Response caching — skip LLM for identical prompts
ENABLE_CACHE = True
CACHE_MAX_SIZE = 64           # LRU cache entries

# Streaming — start processing tokens as they arrive
ENABLE_STREAMING = True

# Thinking mode — Qwen3 models generate <think> tokens before responding.
# Has no effect on Qwen 2.5 Coder, but safe to leave on for model switching.
DISABLE_THINKING = True

# Connection pooling — reuse HTTP connections to LM Studio
HTTP_TIMEOUT = 300            # seconds (5 min — small models can be slow on big code)
HTTP_KEEPALIVE = 30           # keep-alive expiry

# KV Cache optimization — shared prompt prefix across agents
# A common prefix means LM Studio can reuse its KV cache between agents
SHARED_SYSTEM_PREFIX = """You are part of a coding team. Use your tools. Be concise."""

# ── Workspace ─────────────────────────────────────────────
WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)
