"""
Developer Agent — writes actual code, reads specs, implements full programs.

Includes a CODE RESCUE safety net: if the LLM prints code as text instead
of calling write_file (common with small models), we auto-extract code blocks
from the response and write them to workspace/ anyway.
"""

import os
import re
import json
from rich.console import Console
from agent import Agent
from config import WORKSPACE_DIR
import tools as tool_module

console = Console()

SYSTEM_PROMPT = """You are the Developer. Write code files using the write_file tool.

RULES:
1. Call `read_workspace` first to see existing files.
2. To CREATE a new file: call write_file({"path": "workspace/filename.py", "content": "complete code here"}).
3. To MODIFY a file: call read_file first, then call write_file with the full updated content.
4. You MUST call the write_file tool. Do NOT print code as text.
5. Write COMPLETE, WORKING code. No stubs, no TODOs.

CRITICAL — SERVERS (Express, Flask, FastAPI, http.server, etc.):
- NEVER run a server with run_command. It will hang forever and timeout.
- NEVER run `node app.js` or `python3 app.py` if the code starts a server.
- Just write the code files and dependencies. Do NOT try to start the server.
- You CAN run `npm init -y` and `npm install <packages>` — those are fine.
"""

# ── Language → default filename mapping ──
_LANG_TO_FILE = {
    "python": "app.py",         "py": "app.py",
    "javascript": "app.js",     "js": "app.js",
    "typescript": "app.ts",     "ts": "app.ts",
    "go": "main.go",            "rust": "main.rs",
    "java": "Main.java",        "c": "main.c",
    "cpp": "main.cpp",          "c++": "main.cpp",
    "html": "index.html",       "css": "style.css",
    "sh": "script.sh",          "bash": "script.sh",
    "ruby": "app.rb",           "php": "index.php",
}


class DeveloperAgent(Agent):
    """
    Developer with a CODE RESCUE safety net + retry.

    Small models often fail to use tool calls properly. They either:
      A) Print code inside markdown fences (```js ... ```)
      B) Print write_file({"path":..., "content":...}) as plain text
    Both cases are caught and auto-written. If nothing is rescued either,
    we retry ONCE with a very forceful prompt.
    """

    def run(self, task: str, context: str = "") -> str:
        # Snapshot workspace BEFORE running (files + mtimes)
        snap_before = self._workspace_snapshot()

        # Normal agent run (tool-calling loop)
        response = super().run(task, context)

        # Snapshot AFTER running
        snap_after = self._workspace_snapshot()

        # If any files were created, deleted, or modified, all good
        if snap_after != snap_before:
            return response

        # ── CODE RESCUE: try all extraction strategies ──
        rescued = self._rescue_all(response, task)
        if rescued:
            file_list = ", ".join(rescued)
            console.print(f"    [dim]rescued {len(rescued)} file(s): {file_list}[/dim]")
            return response + f"\n\n[Auto-saved to: {file_list}]"

        # ── RETRY: one more attempt with a very forceful nudge ──
        console.print("    [dim]no files written, retrying...[/dim]")
        response2 = self._retry_forceful(task, context)

        snap_after_retry = self._workspace_snapshot()
        if snap_after_retry != snap_before:
            return response2

        # Rescue the retry response too
        rescued2 = self._rescue_all(response2, task)
        if rescued2:
            file_list = ", ".join(rescued2)
            console.print(f"    [dim]rescued {len(rescued2)} file(s) on retry: {file_list}[/dim]")
            return response2 + f"\n\n[Auto-saved to: {file_list}]"

        return response

    def _retry_forceful(self, task: str, context: str) -> str:
        """Re-run with a blunt single-shot prompt that forces a write_file call."""
        import llm
        import config

        system_msg = self.role
        if context:
            system_msg += f"\n\n--- CONTEXT FROM PREVIOUS WORK ---\n{context}"

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": (
                f"{task}\n\n"
                "IMPORTANT: You MUST call write_file NOW with the complete code.\n"
                "Do NOT print code as text. Call the write_file tool."
            )},
        ]
        return llm.chat(
            messages=messages,
            tools=self.tool_schemas if self.tool_schemas else None,
            tool_functions=self.tool_functions,
            agent_name=self.name,
            max_tokens=config.MAX_TOKENS_TOOL_AGENT,
            temperature=config.TEMPERATURE_CODE,
        )

    # ── helpers ──

    @staticmethod
    def _workspace_snapshot() -> dict:
        """Return {filepath: mtime} for all workspace files. Detects creates, edits, and deletes."""
        snap = {}
        if not os.path.exists(WORKSPACE_DIR):
            return snap
        for root, _, files in os.walk(WORKSPACE_DIR):
            for f in files:
                full = os.path.join(root, f)
                try:
                    snap[full] = os.path.getmtime(full)
                except OSError:
                    pass
        return snap

    @staticmethod
    def _workspace_files() -> list[str]:
        """List all files currently in workspace/."""
        found = []
        if not os.path.exists(WORKSPACE_DIR):
            return found
        for root, _, files in os.walk(WORKSPACE_DIR):
            for f in files:
                found.append(os.path.join(root, f))
        return found

    @classmethod
    def _rescue_all(cls, text: str, task: str) -> list[str]:
        """Try all rescue strategies in order: text write_file calls, then fenced blocks."""
        # Strategy 1: Model printed write_file({...}) as plain text
        rescued = cls._rescue_write_file_calls(text)
        if rescued:
            return rescued

        # Strategy 2: Model used markdown code fences
        rescued = cls._rescue_code_blocks(text, task)
        return rescued

    @staticmethod
    def _rescue_write_file_calls(text: str) -> list[str]:
        """
        Extract write_file({"path": "...", "content": "..."}) printed as text.
        The model often outputs the tool call as a string instead of actually calling it.

        If multiple calls target the same file, only the LONGEST content is kept.
        """
        candidates: dict[str, tuple[str, str]] = {}  # path → (full_path, content)

        # Pattern: write_file({ ... "path": "...", "content": "..." ... })
        for match in re.finditer(r'write_file\s*\(\s*\{', text):
            start = match.start()
            # Find the JSON object — count braces
            brace_start = text.index('{', start)
            depth = 0
            end = brace_start
            for i in range(brace_start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break

            json_str = text[brace_start:end]
            try:
                obj = json.loads(json_str)
            except json.JSONDecodeError:
                # Try fixing common issues: single quotes, trailing commas
                try:
                    fixed = json_str.replace("'", '"')
                    fixed = re.sub(r',\s*}', '}', fixed)
                    obj = json.loads(fixed)
                except json.JSONDecodeError:
                    continue

            path = obj.get("path", "")
            content = obj.get("content", "")
            if not path or not content or len(content) < 20:
                continue

            # Ensure path is inside workspace/
            if not path.startswith("workspace/"):
                path = f"workspace/{os.path.basename(path)}"

            # Build absolute path using WORKSPACE_DIR
            basename = path.replace("workspace/", "", 1) if path.startswith("workspace/") else os.path.basename(path)
            full_path = os.path.join(WORKSPACE_DIR, basename)

            # Keep only the LONGEST content per file (avoids stub overwrites)
            if path not in candidates or len(content) > len(candidates[path][1]):
                candidates[path] = (full_path, content)

        # Write the winners
        written = []
        for path, (full_path, content) in candidates.items():
            result = tool_module.write_file(full_path, content)
            console.print(f"    [dim]→ {result}[/dim]")
            written.append(path)

        return written

    @staticmethod
    def _rescue_code_blocks(text: str, task: str) -> list[str]:
        """
        Extract fenced code blocks from the LLM response and write them.

        Filename detection priority:
          1. A path like 'workspace/snake_game.py' in the first line comment
          2. A path like 'workspace/snake_game.py' extracted from the task instruction
          3. The language tag on the fence (```python → app.py)
          4. A keyword-based guess from the task

        If multiple blocks target the same file, only the LONGEST one is kept.
        """
        # Match ```lang\n...code...\n```
        pattern = r"```(\w*)\n(.*?)```"
        blocks = re.findall(pattern, text, re.DOTALL)
        if not blocks:
            return []

        # Try to extract filename from the task instruction
        # e.g. "Create workspace/snake_game.py with a complete snake game"
        task_filename = None
        task_path_match = re.search(r"workspace/([\w./-]+)", task)
        if task_path_match:
            task_filename = task_path_match.group(1)

        # First pass: determine filename and code for each block
        candidates: dict[str, str] = {}  # filename → longest code
        for lang, code in blocks:
            code = code.strip()
            if len(code) < 20:  # skip tiny snippets
                continue

            filename = None

            # Try to find filename in first line comment
            first_line = code.split("\n")[0]
            path_match = re.search(r"(?:workspace/)([\w./-]+)", first_line)
            if path_match:
                filename = path_match.group(1)

            # Use filename from task instruction (highest priority after comment)
            if not filename and task_filename:
                filename = task_filename

            # Try language tag → default filename
            if not filename and lang.lower() in _LANG_TO_FILE:
                filename = _LANG_TO_FILE[lang.lower()]

            # Last resort: guess from task
            if not filename:
                if any(kw in task.lower() for kw in ["express", "node", "server"]):
                    filename = "server.js"
                elif any(kw in task.lower() for kw in ["html", "web page"]):
                    filename = "index.html"
                else:
                    filename = "main.txt"

            # Keep only the LONGEST block per filename
            if filename not in candidates or len(code) > len(candidates[filename]):
                candidates[filename] = code

        # Second pass: write the winners
        written = []
        for filename, code in candidates.items():
            full_path = os.path.join(WORKSPACE_DIR, filename)
            result = tool_module.write_file(full_path, code)
            console.print(f"    [dim]→ {result}[/dim]")
            written.append(f"workspace/{filename}")

        return written


def create() -> Agent:
    return DeveloperAgent(
        name="Developer",
        role=SYSTEM_PROMPT,
        tool_names=["read_workspace", "read_file", "write_file", "list_files", "run_command"],
    )
