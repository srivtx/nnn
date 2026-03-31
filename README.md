# nnn

```
╻ ╻╻ ╻╻ ╻
┃┗┫┃┗┫┃┗┫
╹ ╹╹ ╹╹ ╹
```

A multi-agent coding system that runs on your local machine. Type a task, and a team of AI agents plans, writes, and tests the code for you.

```
> create a snake game with pygame

  1. Developer  Create workspace/snake_game.py with a complete snake game using pygame
  2. BugFixer   Run workspace/snake_game.py with run_command, then fix any errors

  step 1/2 — Developer
    read_workspace →  workspace/
    write_file     →  Wrote 2847 chars to workspace/snake_game.py

  step 2/2 — BugFixer
    run_command    →  (game window opens)
    ✅ No errors found.
```

---

## What is this?

**nnn** is a ~1500-line Python project that builds a complete AI agent system from scratch. It uses [LM Studio](https://lmstudio.ai) to run a local language model and connects 5 specialized AI agents that collaborate to complete coding tasks.

The agents:

| Agent           | Job                                       |
| --------------- | ----------------------------------------- |
| **Architect**   | Designs system structure and writes plans |
| **Developer**   | Reads plans and writes working code       |
| **BugFixer**    | Runs code, finds errors, and fixes them   |
| **Researcher**  | Analyzes existing code in the workspace   |
| **WebSearcher** | Searches the internet for documentation   |

They are not separate programs — they are the same AI model called with different instructions and different tools.

---

## Quick Start

### 1. Install LM Studio

Download [LM Studio](https://lmstudio.ai), load any model (Qwen 2.5 Coder 7B or higher recommended), and start the local server.

### 2. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/nnn.git
cd nnn
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 3. Run

```bash
nnn
```

That's it. Type a task and press Enter.

**One-shot mode:**

```bash
nnn "create a flask API with user login"
```

---

## How It Works

```
You type a task
     ↓
Orchestrator asks the LLM: "Break this into steps and assign agents"
     ↓
LLM returns a JSON plan:  Developer → BugFixer
     ↓
Each agent runs in order, using tools (read/write files, run commands)
     ↓
You get working code in the workspace/ folder
```

There is only **one AI model** running. Each "agent" is just the same model called with a different system prompt and a different set of tools. For a deeper explanation, see [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md).

---

## Learn How to Build This

This project comes with **12 step-by-step lessons** that teach you how to build the entire system from scratch. Each lesson adds one concept, and you test it before moving on.

| #   | Lesson                                                  | What you build                                            |
| --- | ------------------------------------------------------- | --------------------------------------------------------- |
| 01  | [Talking to an AI Model](docs/01_talking_to_ai.md)      | Send a message to LM Studio and get a reply               |
| 02  | [Giving the AI a Role](docs/02_giving_the_ai_a_role.md) | System prompts, multi-turn conversation                   |
| 03  | [Tool Calling](docs/03_tool_calling.md)                 | AI calls real Python functions (read files, run commands) |
| 04  | [Your First Agent Class](docs/04_your_first_agent.md)   | Package role + tools + loop into a reusable Agent         |
| 05  | [Multiple Agents](docs/05_multiple_agents.md)           | 2 agents → 3 agents, passing context between them         |
| 06  | [The Orchestrator](docs/06_the_orchestrator.md)         | AI decides which agents to run and in what order          |
| 07  | [The Full System](docs/07_the_full_system.md)           | Add remaining tools + WebSearcher + Researcher            |
| 08  | [Debugging Failures](docs/08_debugging_failures.md)     | Real failure cases and how to fix them                    |
| 09  | [Speed & Context](docs/09_speed_and_context.md)         | 6 optimizations: caching, streaming, parallel execution   |
| 10  | [Surgical Editing](docs/10_surgical_editing.md)         | Line-by-line editing tools (edit_lines, insert_code)      |
| 11  | [Small-Model Safety](docs/11_small_model_safety.md)     | Safety nets for 3-4B models that fail often               |
| 12  | [CLI & Packaging](docs/12_cli_and_packaging.md)         | Turn it into an installable `nnn` command                 |

Start at Lesson 01. Each lesson builds on the previous one. By Lesson 12 you have the complete system.

**New to programming?** Start with [docs/BEGINNER_GUIDE.md](docs/BEGINNER_GUIDE.md) instead — it's a gentler introduction.

---

## Project Structure

```
nnn/
├── main.py              ← entry point (REPL + one-shot mode)
├── orchestrator.py      ← plans tasks and delegates to agents
├── agent.py             ← base Agent class
├── llm.py               ← LLM bridge (tool-calling loop, streaming, caching)
├── tools.py             ← all tool implementations (read/write files, run commands, web search)
├── config.py            ← settings (server URL, token limits, temperatures)
├── agents/
│   ├── architect.py     ← system designer
│   ├── developer.py     ← code writer (with rescue safety nets)
│   ├── bug_fixer.py     ← run → diagnose → fix → verify
│   ├── researcher.py    ← code analyzer
│   └── web_searcher.py  ← internet search
├── workspace/           ← where agents write code (shared workspace)
├── docs/                ← 12 step-by-step lessons
├── pyproject.toml       ← package config
└── requirements.txt     ← dependencies
```

---

## Requirements

- Python 3.10+
- [LM Studio](https://lmstudio.ai) with any loaded model
- Recommended: Qwen 2.5 Coder 7B+ or Qwen 3 8B+ for best results
- Works with 3-4B models too (with safety nets — see Lesson 11)

---

## Configuration

All settings are in `config.py`:

```python
LM_BASE_URL = "http://localhost:1234/v1"   # LM Studio server
MAX_TOKENS = 8192                           # max response length
TEMPERATURE_CODE = 0.3                      # lower = more reliable tool use
PARALLEL_AGENTS = True                      # run independent agents concurrently
```

Override with environment variables:

```bash
LM_BASE_URL=http://192.168.1.5:1234/v1 nnn "build a todo app"
```

---

## License

MIT
