"""
Orchestrator — takes a user task, breaks it down, and delegates to the specialized agents.

SPEED OPTIMIZATIONS:
  1. Parallel agent execution — independent steps run concurrently
  2. Adaptive max_tokens — planning/summary calls use smaller limits
  3. Dependency graph — automatically detects which steps can overlap
  4. KV cache prefix sharing — all agents share a common prompt prefix
"""

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console

import llm
import agents.architect
import agents.researcher
import agents.web_searcher
import agents.bug_fixer
import agents.developer
from config import WORKSPACE_DIR
import config

console = Console()

# Initialize our specialized agents
TEAM = {
    "Architect": agents.architect.create(),
    "Researcher": agents.researcher.create(),
    "WebSearcher": agents.web_searcher.create(),
    "Developer": agents.developer.create(),
    "BugFixer": agents.bug_fixer.create(),
}


def _list_workspace_files() -> str:
    """List files in workspace/ for context."""
    workspace = config.WORKSPACE_DIR
    if not os.path.exists(workspace):
        return ""
    files = []
    for root, _, filenames in os.walk(workspace):
        for f in filenames:
            rel = os.path.relpath(os.path.join(root, f), workspace)
            files.append(rel)
    return ", ".join(sorted(files)) if files else ""


def run_task(task: str):
    """
    Main entry point for a user task.
    The Orchestrator acts as a router/coordinator.

    Speed: uses parallel execution for independent steps + adaptive token limits.
    """
    task_start = time.time()

    # 0. Analyze the project first — detect language, runtime, framework
    project = _analyze_project(task)
    if project.get("language"):
        console.print(f"  [dim]detected:[/dim] {project.get('language', '?')} · {project.get('runtime', '?')} · {project.get('framework') or 'no framework'}")

    # 1. Ask the Orchestrator (LLM) to make a plan and pick agents
    #    Uses smaller max_tokens since plan output is compact JSON
    plan = _create_plan(task, project)
    
    if not plan or not plan.get("steps"):
        console.print("  [red]failed to create plan[/red]")
        return

    # SAFETY: Programmatically strip BugFixer steps for servers
    # Small models ignore prompt-level warnings, so we enforce it in code
    if project.get("is_server"):
        original_count = len(plan["steps"])
        plan["steps"] = [s for s in plan["steps"] if s.get("agent") != "BugFixer"]
        removed = original_count - len(plan["steps"])
        if removed:
            console.print(f"  [dim]server detected — removed {removed} BugFixer step(s)[/dim]")

    # Show plan
    console.print()
    for i, step in enumerate(plan["steps"], 1):
        agent = step.get("agent", "?")
        instr = step.get('instruction', '')[:60]
        console.print(f"  [dim]{i}.[/dim] [bold]{agent}[/bold] [dim]{instr}[/dim]")
    console.print()
    
    # Track what has happened so far to pass as context
    # Include existing workspace files so agents know what's already there
    existing_files = _list_workspace_files()
    workspace_context = f"Main Task: {task}\n\n"
    
    # Include project analysis so agents know language/runtime/server status
    if project.get("language"):
        workspace_context += f"Project: {project.get('language')} · runtime: {project.get('runtime')} · framework: {project.get('framework') or 'none'}\n"
    if project.get("is_server"):
        workspace_context += "WARNING: This is a SERVER. Do NOT run it with run_command — it will timeout forever. Only write code, do not run it.\n"
    workspace_context += "\n"
    
    if existing_files:
        workspace_context += f"Existing files in workspace:\n{existing_files}\n\n"
    workspace_context += "Execution Log:\n"
    
    # 2. Build a dependency graph and execute steps
    #    Independent steps run in PARALLEL; dependent steps run sequentially
    if config.PARALLEL_AGENTS and len(plan["steps"]) > 1:
        workspace_context = _execute_parallel(plan["steps"], task, workspace_context)
    else:
        workspace_context = _execute_sequential(plan["steps"], workspace_context)

    # 3. Final synthesis (uses smaller max_tokens)
    _generate_final_summary(task, workspace_context)

    # Compact stats line
    elapsed = time.time() - task_start
    cache_stats = llm.get_cache_stats()
    console.print()
    console.print(f"  [dim]{elapsed:.1f}s · {len(plan['steps'])} steps · cache {cache_stats['hits']}/{cache_stats['hits']+cache_stats['misses']}[/dim]")
    console.print()


def _execute_sequential(steps: list[dict], workspace_context: str) -> str:
    """Execute steps one by one (original behavior, fallback)."""
    for i, step in enumerate(steps, 1):
        agent_name = step.get("agent")
        instruction = step.get("instruction")
        
        console.print(f"  [dim]step {i}/{len(steps)}[/dim]")
        
        if agent_name not in TEAM:
            console.print(f"    [red]unknown agent '{agent_name}'[/red]")
            workspace_context += f"Step {i}: Assigned to {agent_name}, but agent not found. Failed.\n"
            continue
            
        agent = TEAM[agent_name]
        trimmed_context = _compress_context(workspace_context) if len(workspace_context) > 1200 else workspace_context
        try:
            result = agent.run(task=instruction, context=trimmed_context)
            workspace_context += f"Step {i} ({agent_name}): {instruction}\nResult: {result[:500]}\n\n"
        except Exception as e:
            console.print(f"    [red]agent failed: {e}[/red]")
            workspace_context += f"Step {i} ({agent_name}): Failed with error: {e}\n\n"
    return workspace_context


def _execute_parallel(steps: list[dict], task: str, workspace_context: str) -> str:
    """
    Execute steps with automatic parallelism.
    
    Strategy: group steps into "waves". Within each wave, all steps run concurrently.
    A step depends on the previous step if:
      - It uses output from a prior agent (e.g., Developer depends on Architect)
      - It's a BugFixer (always runs after Developer)
    
    Independent steps (e.g., Researcher + WebSearcher) run in parallel.
    """
    # Build dependency waves
    waves = _build_execution_waves(steps)
    
    total_steps = len(steps)
    step_counter = 0
    
    for wave_idx, wave in enumerate(waves):
        if len(wave) == 1:
            # Single step — run inline (no thread overhead)
            step_counter += 1
            step = wave[0]
            agent_name = step.get("agent")
            instruction = step.get("instruction")
            
            console.print(f"  [dim]step {step_counter}/{total_steps}[/dim]")
            
            if agent_name not in TEAM:
                workspace_context += f"Step {step_counter}: Unknown agent '{agent_name}'. Skipped.\n"
                continue
            
            agent = TEAM[agent_name]
            trimmed_context = _compress_context(workspace_context) if len(workspace_context) > 1200 else workspace_context
            try:
                result = agent.run(task=instruction, context=trimmed_context)
                workspace_context += f"Step {step_counter} ({agent_name}): {instruction}\nResult: {result[:500]}\n\n"
            except Exception as e:
                console.print(f"    [red]agent failed: {e}[/red]")
                workspace_context += f"Step {step_counter} ({agent_name}): Failed: {e}\n\n"
        else:
            # PARALLEL wave — run all steps concurrently
            agent_names = [s.get("agent") for s in wave]
            console.print(f"  [dim]parallel[/dim] [bold]{', '.join(agent_names)}[/bold]")
            
            trimmed_context = _compress_context(workspace_context) if len(workspace_context) > 1200 else workspace_context
            results = {}
            
            with ThreadPoolExecutor(max_workers=config.MAX_PARALLEL_WORKERS) as pool:
                futures = {}
                for step in wave:
                    step_counter += 1
                    a_name = step.get("agent")
                    instr = step.get("instruction")
                    if a_name not in TEAM:
                        workspace_context += f"Step {step_counter}: Unknown agent '{a_name}'. Skipped.\n"
                        continue
                    agent = TEAM[a_name]
                    fut = pool.submit(_run_agent_safe, agent, instr, trimmed_context)
                    futures[fut] = (step_counter, a_name, instr)
                
                for future in as_completed(futures):
                    sc, a_name, instr = futures[future]
                    result = future.result()
                    workspace_context += f"Step {sc} ({a_name}): {instr}\nResult: {result[:500]}\n\n"

    return workspace_context


def _run_agent_safe(agent, instruction: str, context: str) -> str:
    """Run an agent with error handling (for use in thread pool)."""
    try:
        return agent.run(task=instruction, context=context)
    except Exception as e:
        return f"Failed with error: {e}"


def _build_execution_waves(steps: list[dict]) -> list[list[dict]]:
    """
    Group steps into parallel execution waves based on dependencies.
    
    Rules:
      - BugFixer always depends on Developer
      - Developer depends on Architect (if present)
      - Researcher and WebSearcher are independent of each other
      - Steps within the same wave have no dependencies → run in parallel
    """
    # Define agent dependency: agent → set of agents it must wait for
    DEPENDS_ON = {
        "Developer": {"Architect", "Researcher", "WebSearcher"},
        "BugFixer": {"Developer"},
    }
    
    waves = []
    current_wave = []
    completed_agents = set()
    
    for step in steps:
        agent = step.get("agent", "")
        deps = DEPENDS_ON.get(agent, set())
        
        # Check if all dependencies are satisfied by previously completed waves
        unmet = deps - completed_agents
        
        if unmet and current_wave:
            # Flush current wave, start new one
            waves.append(current_wave)
            for s in current_wave:
                completed_agents.add(s.get("agent", ""))
            current_wave = [step]
        else:
            current_wave.append(step)
    
    if current_wave:
        waves.append(current_wave)
    
    return waves


def _analyze_project(task: str) -> dict:
    """
    Analyze the workspace and task to detect language, runtime, and framework
    BEFORE planning. This gives the orchestrator accurate context.
    """
    files = _list_workspace_files()
    
    if not files:
        # No existing project — infer from task keywords
        return _infer_from_task(task)
    
    profile = {"files": files, "language": None, "runtime": None, "framework": None, "is_server": False}
    
    # Detect language from file extensions
    extensions = {os.path.splitext(f.strip())[1] for f in files.split(",")}
    RUNTIME_MAP = {
        ".py":   ("python",     "python3"),
        ".js":   ("javascript", "node"),
        ".ts":   ("typescript", "npx tsx"),
        ".go":   ("go",         "go run"),
        ".rs":   ("rust",       "cargo run"),
        ".java": ("java",       "javac && java"),
        ".c":    ("c",          "gcc -o out && ./out"),
        ".cpp":  ("c++",        "g++ -o out && ./out"),
    }
    for ext, (lang, runtime) in RUNTIME_MAP.items():
        if ext in extensions:
            profile["language"] = lang
            profile["runtime"] = runtime
            break
    
    # Detect framework by reading key files
    pkg_json = os.path.join(WORKSPACE_DIR, "package.json")
    if os.path.exists(pkg_json):
        try:
            with open(pkg_json) as f:
                pkg = json.loads(f.read())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "express" in deps:
                profile["framework"] = "express"
                profile["is_server"] = True
            elif "fastify" in deps:
                profile["framework"] = "fastify"
                profile["is_server"] = True
            elif "next" in deps:
                profile["framework"] = "next.js"
                profile["is_server"] = True
        except Exception:
            pass
    
    # Check for server-like imports in main files
    SERVER_KEYWORDS = ["express", "flask", "fastapi", "http.server", "createServer", "app.listen", "uvicorn"]
    for fname in files.split(","):
        fpath = os.path.join(WORKSPACE_DIR, fname.strip())
        if os.path.isfile(fpath):
            try:
                with open(fpath, "r", errors="replace") as f:
                    head = f.read(2000)
                if any(kw in head for kw in SERVER_KEYWORDS):
                    profile["is_server"] = True
                    # Try to detect framework from imports
                    if not profile["framework"]:
                        for kw in ["express", "flask", "fastapi", "django"]:
                            if kw in head.lower():
                                profile["framework"] = kw
                                break
                    break
            except Exception:
                pass
    
    return profile


def _infer_from_task(task: str) -> dict:
    """Detect language/runtime/framework from task keywords when workspace is empty."""
    t = task.lower()
    profile = {"files": "", "language": None, "runtime": None, "framework": None, "is_server": False}
    
    # JavaScript / Node
    if any(kw in t for kw in ["express", "node", "javascript", " js ", ".js"]):
        profile["language"] = "javascript"
        profile["runtime"] = "node"
        if "express" in t:
            profile["framework"] = "express"
            profile["is_server"] = True
    # TypeScript
    elif any(kw in t for kw in ["typescript", " ts ", ".ts"]):
        profile["language"] = "typescript"
        profile["runtime"] = "npx tsx"
    # Python
    elif any(kw in t for kw in ["python", "flask", "django", "fastapi"]):
        profile["language"] = "python"
        profile["runtime"] = "python3"
        for fw in ["flask", "django", "fastapi"]:
            if fw in t:
                profile["framework"] = fw
                profile["is_server"] = True
    # Go
    elif any(kw in t for kw in ["golang", " go "]):
        profile["language"] = "go"
        profile["runtime"] = "go run"
    # Rust
    elif "rust" in t:
        profile["language"] = "rust"
        profile["runtime"] = "cargo run"
    # Default to Python
    else:
        profile["language"] = "python"
        profile["runtime"] = "python3"
    
    # Detect generic server tasks
    if any(kw in t for kw in ["server", "api", "rest", "endpoint", "http"]):
        profile["is_server"] = True
    
    return profile


def _create_plan(task: str, project: dict | None = None) -> dict:
    """Ask the LLM to break the task into agent assignments."""
    # Build project context block
    project = project or {}
    lang = project.get("language", "python")
    runtime = project.get("runtime", "python3")
    framework = project.get("framework") or "none"
    is_server = project.get("is_server", False)
    
    server_note = ""
    if is_server:
        server_note = (
            "\n** THIS IS A SERVER / LONG-RUNNING PROCESS. "
            "Do NOT add BugFixer — it will timeout. Developer only. **\n"
        )

    system_prompt = f"""You are the Orchestrator. Break the task into steps and assign agents.

Project Analysis:
- Language: {lang}
- Runtime: {runtime}
- Framework: {framework}
- Is Server: {is_server}
{server_note}
Agents:
- Developer: Writes or modifies code. USE for all coding tasks.
- BugFixer: Runs code with run_command, finds errors, fixes them. USE after Developer.
- Architect: Designs multi-file systems. USE only for complex projects.
- Researcher: Analyzes existing code in workspace/. USE only when asked to review.
- WebSearcher: Searches the internet. USE only when user says "search" or "look up".

RULES:
- "Create X" or "Build X" = Developer + BugFixer (2 steps). ALWAYS add BugFixer to test after creating code.
- EXCEPTION: Do NOT add BugFixer for servers or long-running processes (Express, Flask, FastAPI, http.server, etc.) — they timeout. Use Developer only.
- For coding tasks, NEVER add WebSearcher or Researcher.
- Tell Developer the exact filename: "Create workspace/<filename> with a complete <description>."
- Tell BugFixer: "Run workspace/<filename> with {runtime} (NOT python3 unless it's Python), then fix any errors."
- For .js files, BugFixer must use: node filename.js
- For .ts files, BugFixer must use: npx tsx filename.ts
- For .py files, BugFixer must use: python3 filename.py
- If user asks to modify existing code, tell Developer: "Read workspace/filename with read_file, then rewrite it with write_file including the changes."

Output ONLY valid JSON:
{{
  "steps": [
    {{"agent": "Developer", "instruction": "Create workspace/app.py with a complete ..."}},
    {{"agent": "BugFixer", "instruction": "Run workspace/app.py with {runtime}, then fix any errors."}}
  ]
}}
"""
    
    existing = _list_workspace_files()
    user_msg = task
    if existing:
        user_msg = f"Existing files in workspace: {existing}\n\nTask: {task}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg}
    ]
    
    # We don't give the orchestrator any tools here, just ask for JSON
    # Speed: plan is compact JSON, use smaller max_tokens
    response = llm.chat(messages, agent_name="Orchestrator", max_tokens=config.MAX_TOKENS_PLAN, stream=False)
    
    # Try to parse the output as JSON
    try:
        # Strip markdown code blocks if the LLM added them
        cleanup = response.replace("```json", "").replace("```", "").strip()
        return json.loads(cleanup)
    except json.JSONDecodeError:
        # Fallback: extract first JSON object from surrounding prose
        match = re.search(r'\{.*\}', cleanup, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        console.print(f"  [red]failed to parse plan[/red] [dim]{response[:120]}[/dim]")
        return {}


def _generate_final_summary(task: str, context: str):
    """Generate a final summary of what was accomplished."""
    system_prompt = """You are the Orchestrator. Agents have finished.
Write a VERY short summary (3-5 sentences max). Include:
1. What was built (one sentence)
2. Files created (list filenames only)
3. One next step
No emojis. No tables. No filler. Be direct.
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Task: {task}\n\nExecution Log:\n{context}"}
    ]
    
    # Speed: summaries are short, use smaller max_tokens
    summary = llm.chat(messages, agent_name="Orchestrator", max_tokens=config.MAX_TOKENS_SUMMARY, stream=False)
    
    console.print()
    console.print(f"  {summary}")


def _compress_context(context: str) -> str:
    """
    When the running context log gets too large to pass to an agent,
    use the LLM to summarize it into a compact bullet-point digest.
    This preserves all the key facts (which files were created, what
    was found, what decisions were made) without blowing the context window.
    """
    console.print("    [dim]compressing context...[/dim]")
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are a context compressor. Your job is to compress an execution log into a very short, "
                "dense bullet-point summary. Keep every important fact: file names, decisions made, results, "
                "errors encountered, and what still needs to be done. Be extremely concise — aim for under 400 words. "
                "Output ONLY the compressed summary, nothing else."
            )
        },
        {
            "role": "user",
            "content": f"Compress this execution log:\n\n{context}"
        }
    ]
    
    try:
        # Speed: compression output is short, use smaller max_tokens
        compressed = llm.chat(messages, agent_name="Compressor", max_tokens=config.MAX_TOKENS_SUMMARY, stream=False)
        console.print(f"    [dim]compressed {len(context)} → {len(compressed)} chars[/dim]")
        return compressed
    except Exception:
        # If compression fails, fall back to simple tail-truncation
        return context[-1200:]


def maybe_clean_workspace():
    """Ask the user whether to clean workspace/ if it already has files."""
    import shutil
    os.makedirs(WORKSPACE_DIR, exist_ok=True)

    existing = os.listdir(WORKSPACE_DIR)
    if not existing:
        return  # nothing to clean

    file_list = ", ".join(existing[:6])
    if len(existing) > 6:
        file_list += f" (+{len(existing) - 6} more)"

    console.print(f"  [dim]workspace has files:[/dim] {file_list}")
    answer = console.input("  [bold]clean workspace?[/bold] [dim](y/N)[/dim] ").strip().lower()

    if answer in ("y", "yes"):
        for item in existing:
            path = os.path.join(WORKSPACE_DIR, item)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except Exception:
                pass
        console.print("  [dim]cleaned[/dim]")
    else:
        console.print("  [dim]keeping existing files[/dim]")

