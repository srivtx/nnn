"""
Tools that agents can use.
Each tool has:
  1. An implementation (plain Python function)
  2. An OpenAI-format JSON schema describing it for the LLM
"""

import os
import json
import subprocess
import httpx
from config import WORKSPACE_DIR


def _resolve_path(path: str) -> str:
    """Normalize any workspace-relative path to an absolute path.
    
    Agents often pass 'workspace/file.py' as a relative path. If the user
    runs nnn from a different directory, that relative path breaks.
    This converts any path starting with 'workspace/' to use the absolute
    WORKSPACE_DIR so tools work regardless of CWD.
    
    Also handles:
      'workspace' (no slash) → WORKSPACE_DIR
      '.'                    → WORKSPACE_DIR  (agents treat workspace as cwd)
    """
    path = os.path.expanduser(path)
    if path in ("workspace", ".", "./"):
        return WORKSPACE_DIR
    if path.startswith("workspace/"):
        return os.path.join(WORKSPACE_DIR, path[len("workspace/"):])
    if path.startswith("./"):
        return os.path.join(WORKSPACE_DIR, path[2:])
    return path


# ═══════════════════════════════════════════════════════════
#  FILE SYSTEM TOOLS
# ═══════════════════════════════════════════════════════════

def read_file(path: str) -> str:
    """Read the contents of a file with line numbers."""
    path = _resolve_path(path)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        # Show line numbers so agents can use edit_lines
        numbered = []
        for i, line in enumerate(lines, 1):
            numbered.append(f"{i:4d} | {line.rstrip()}")
        content = "\n".join(numbered)
        # cap at ~8k chars so we don't blow context
        if len(content) > 8000:
            return content[:8000] + f"\n\n... (truncated, {len(lines)} lines total)"
        return content
    except Exception as e:
        return f"Error reading {path}: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates parent directories if needed."""
    path = _resolve_path(path)
    # Strip markdown fences that small models accidentally include in content
    if content.startswith("```"):
        lines = content.split("\n")
        # Remove first line (```python or ```) and last line (```)
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Wrote {len(content)} chars to {path}"
    except Exception as e:
        return f"Error writing {path}: {e}"


def delete_file(path: str) -> str:
    """Delete a file from the workspace."""
    path = _resolve_path(path)
    try:
        os.remove(path)
        return f"Deleted {path}"
    except FileNotFoundError:
        return f"Error: {path} does not exist"
    except Exception as e:
        return f"Error deleting {path}: {e}"


def edit_file(path: str, old_code: str, new_code: str) -> str:
    """Replace a specific section of code in an existing file.
    
    Use this instead of write_file when you only need to change part of a file.
    The old_code must match exactly (including whitespace).
    """
    path = _resolve_path(path)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except FileNotFoundError:
        return f"Error: {path} does not exist. Use write_file to create new files."
    except Exception as e:
        return f"Error reading {path}: {e}"

    # Try exact match first
    if old_code in content:
        new_content = content.replace(old_code, new_code, 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"Edited {path} — replaced {len(old_code)} chars with {len(new_code)} chars"

    # Try with stripped whitespace (fuzzy match)
    old_stripped = old_code.strip()
    if old_stripped and old_stripped in content:
        new_content = content.replace(old_stripped, new_code.strip(), 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"Edited {path} (fuzzy match) — replaced section"

    return f"Error: could not find the old_code section in {path}. Use edit_lines with line numbers instead."


def edit_lines(path: str, start_line: int, end_line: int, new_code: str) -> str:
    """Replace lines start_line through end_line (inclusive) with new_code.
    
    Line numbers are 1-based (as shown by read_file). Use this when edit_file fails
    or when you know the exact line range to replace.
    Pass empty new_code to delete lines.
    """
    # Cast in case the LLM sends "5" instead of 5
    try:
        start_line = int(start_line)
        end_line = int(end_line)
    except (ValueError, TypeError):
        return f"Error: start_line and end_line must be integers"

    path = _resolve_path(path)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return f"Error: {path} does not exist."
    except Exception as e:
        return f"Error reading {path}: {e}"

    total = len(lines)
    if start_line < 1 or end_line < start_line or start_line > total:
        return f"Error: invalid line range {start_line}-{end_line} (file has {total} lines)"
    # Clamp end_line
    end_line = min(end_line, total)

    # Build new content
    before = lines[:start_line - 1]
    after = lines[end_line:]

    # Split new_code into lines, handling trailing newline artifact
    if not new_code or new_code.strip() == "":
        new_with_newlines = []  # delete lines
    else:
        new_lines = new_code.split("\n")
        # Remove trailing empty string from split (artifact of trailing \n)
        if new_lines and new_lines[-1] == "":
            new_lines.pop()
        new_with_newlines = [l + "\n" for l in new_lines]

    result = before + new_with_newlines + after
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(result)
    replaced = len(new_with_newlines)
    return f"Edited {path} lines {start_line}-{end_line} → {replaced} new lines"


def insert_code(path: str, position: str, code: str) -> str:
    """Insert code at a specific position in an existing file.
    
    Args:
        path: File to modify
        position: 'top', 'bottom', or a line number (inserts AFTER that line, use '0' for very top)
        code: Code to insert
    """
    path = _resolve_path(path)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return f"Error: {path} does not exist. Use write_file to create new files."
    except Exception as e:
        return f"Error reading {path}: {e}"

    pos = position.strip().lower()
    if pos == "top":
        new_lines = code.rstrip("\n").split("\n")
        new_with_nl = [l + "\n" for l in new_lines]
        result = new_with_nl + lines
    elif pos == "bottom":
        new_lines = code.rstrip("\n").split("\n")
        new_with_nl = [l + "\n" for l in new_lines]
        result = lines + ["\n"] + new_with_nl
    else:
        # Line number — insert AFTER that line
        try:
            line_num = int(pos)
        except ValueError:
            return f"Error: position must be 'top', 'bottom', or a line number, got '{position}'"
        if line_num < 0 or line_num > len(lines):
            return f"Error: line {line_num} out of range (file has {len(lines)} lines)"
        new_lines = code.rstrip("\n").split("\n")
        new_with_nl = [l + "\n" for l in new_lines]
        result = lines[:line_num] + new_with_nl + lines[line_num:]

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(result)
    code_lines = len(code.rstrip("\n").split("\n"))
    return f"Inserted {code_lines} lines at {position} of {path}"


def list_files(directory: str = WORKSPACE_DIR) -> str:
    """List files and directories recursively (max depth 3)."""
    directory = _resolve_path(directory)
    results = []
    try:
        for root, dirs, files in os.walk(directory):
            depth = root.replace(directory, "").count(os.sep)
            if depth >= 3:
                dirs.clear()
                continue
            indent = "  " * depth
            results.append(f"{indent}{os.path.basename(root)}/")
            for f in sorted(files)[:50]:  # cap per directory
                results.append(f"{indent}  {f}")
        return "\n".join(results[:200]) or "Empty directory"
    except Exception as e:
        return f"Error listing {directory}: {e}"


def search_code(pattern: str, directory: str = "workspace") -> str:
    """Search for a text pattern in files using grep."""
    directory = _resolve_path(directory)
    try:
        result = subprocess.run(
            ["grep", "-rnI",
             "--exclude-dir=venv", "--exclude-dir=.git",
             "--exclude-dir=__pycache__", "--exclude-dir=node_modules",
             "--include=*.py", "--include=*.js", "--include=*.ts",
             "--include=*.java", "--include=*.go", "--include=*.rs", "--include=*.c",
             "--include=*.cpp", "--include=*.h", "--include=*.md", "--include=*.txt",
             "--include=*.json", "--include=*.yaml", "--include=*.yml",
             "--include=*.html", "--include=*.css",
             pattern, directory],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout.strip()
        if not output:
            return f"No matches found for '{pattern}'"
        lines = output.split("\n")
        if len(lines) > 30:
            return "\n".join(lines[:30]) + f"\n\n... ({len(lines)} matches total)"
        return output
    except Exception as e:
        return f"Search error: {e}"


# ═══════════════════════════════════════════════════════════
#  EXECUTION TOOLS
# ═══════════════════════════════════════════════════════════

def run_command(command: str, cwd: str = WORKSPACE_DIR) -> str:
    """Run a shell command and return its output."""
    cwd = _resolve_path(cwd)
    
    # Guard: detect server launches that will hang forever
    # e.g. "node app.js", "python3 server.py" on files with app.listen/Flask
    SERVER_PATTERNS = ["app.listen", "createServer", ".listen(", "uvicorn", "flask", "fastapi", "http.server"]
    cmd_parts = command.strip().split()
    if len(cmd_parts) >= 2 and cmd_parts[0] in ("node", "python3", "python"):
        target_file = cmd_parts[-1]
        # Resolve the file path
        check_path = os.path.join(cwd, target_file) if not os.path.isabs(target_file) else target_file
        if os.path.isfile(check_path):
            try:
                with open(check_path, "r", errors="replace") as f:
                    content = f.read(3000)
                if any(pat in content for pat in SERVER_PATTERNS):
                    return (
                        f"REFUSED: {target_file} is a server (contains listener). "
                        "Running it would hang forever. Do NOT run servers with run_command. "
                        "The code is already written — just verify it by reading the file."
                    )
            except Exception:
                pass
    
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=30, cwd=cwd
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += "\nSTDERR:\n" + result.stderr
        if result.returncode != 0:
            output += f"\n(exit code: {result.returncode})"
        output = output.strip()
        if len(output) > 4000:
            output = output[:4000] + "\n... (truncated)"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30s — this is likely a server or long-running process. Do NOT retry."
    except Exception as e:
        return f"Command error: {e}"


# ═══════════════════════════════════════════════════════════
#  WEB TOOLS
# ═══════════════════════════════════════════════════════════

def web_search(query: str) -> str:
    """Search the web using DuckDuckGo (no API key needed)."""
    import re
    # Truncate overly long queries — DDG chokes on them
    query = " ".join(query.split()[:8])
    results = []

    # Method 1: DuckDuckGo Instant Answer JSON API
    try:
        resp = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_redirect": "1", "no_html": "1"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
            follow_redirects=True,
        )
        data = resp.json()
        # Pull from AbstractText, RelatedTopics
        if data.get("AbstractText"):
            results.append(f"Summary: {data['AbstractText']}\nSource: {data.get('AbstractURL','')}\n")
        for topic in data.get("RelatedTopics", [])[:6]:
            if isinstance(topic, dict) and topic.get("Text"):
                url = topic.get("FirstURL", "")
                results.append(f"- {topic['Text']}\n  {url}\n")
    except Exception:
        pass

    # Method 2: Fallback — scrape HTML version
    if not results:
        try:
            resp = httpx.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
                timeout=15,
                follow_redirects=True,
            )
            text = resp.text
            # Try multiple class name patterns (DDG changes them)
            titles   = re.findall(r'class="[^"]*result[^"]*a[^"]*"[^>]*>(.*?)</a', text, re.DOTALL)
            snippets = re.findall(r'class="[^"]*snippet[^"]*"[^>]*>(.*?)</(?:a|span|div)', text, re.DOTALL)
            for i, (t, s) in enumerate(zip(titles[:6], snippets[:6])):
                ct = re.sub(r'<[^>]+>', '', t).strip()
                cs = re.sub(r'<[^>]+>', '', s).strip()
                if ct and cs:
                    results.append(f"{i+1}. {ct}\n   {cs}\n")
        except Exception as e:
            return f"Web search error: {e}"

    return "\n".join(results) if results else "No results found. Try read_url with a specific URL instead."


def read_url(url: str) -> str:
    """Fetch the text content of a URL."""
    try:
        resp = httpx.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
            follow_redirects=True,
        )
        # Simple HTML to text: strip tags
        import re
        text = re.sub(r'<script[^>]*>.*?</script>', '', resp.text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 1500:
            text = text[:1500] + "\n... (truncated)"
        return text
    except Exception as e:
        return f"Error fetching URL: {e}"


# ═════════════════════════════════════════════════════
#  WORKSPACE TOOLS
# ════════════════════════════════════════════════════

def write_plan(filename: str, content: str) -> str:
    """Write a plan or notes to the shared workspace."""
    path = os.path.join(WORKSPACE_DIR, filename)
    return write_file(path, content)


def read_workspace(filename: str = "") -> str:
    """Read a file from the shared workspace, or list all workspace files."""
    if not filename:
        return list_files(WORKSPACE_DIR)
    path = os.path.join(WORKSPACE_DIR, filename)
    return read_file(path)


# ═══════════════════════════════════════════════════════════
#  TOOL SCHEMAS (OpenAI function-calling format)
# ═══════════════════════════════════════════════════════════

TOOL_SCHEMAS = {
    "read_file": {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file at the given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to read"}
                },
                "required": ["path"]
            }
        }
    },
    "write_file": {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates parent directories if needed. WARNING: This OVERWRITES the entire file. To change only part of a file, use edit_file instead.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to write"},
                    "content": {"type": "string", "description": "Content to write to the file"}
                },
                "required": ["path", "content"]
            }
        }
    },    "delete_file": {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file. Use this to remove unwanted files from the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to delete"}
                },
                "required": ["path"]
            }
        }
    },    "edit_file": {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace a specific section of code in an existing file. The old_code must match text in the file exactly. If this fails, use edit_lines instead.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to edit"},
                    "old_code": {"type": "string", "description": "The exact existing code to find and replace"},
                    "new_code": {"type": "string", "description": "The new code to replace it with"}
                },
                "required": ["path", "old_code", "new_code"]
            }
        }
    },
    "edit_lines": {
        "type": "function",
        "function": {
            "name": "edit_lines",
            "description": "REPLACE specific lines in a file. Use read_file first to see line numbers, then specify which lines to replace. To DELETE lines, set new_code to empty string. This is the MOST RELIABLE way to edit existing files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file (e.g. workspace/app.py)"},
                    "start_line": {"type": "integer", "description": "First line to replace (1-based, from read_file output)"},
                    "end_line": {"type": "integer", "description": "Last line to replace (inclusive, 1-based)"},
                    "new_code": {"type": "string", "description": "New code to replace those lines with. Use empty string to delete lines."}
                },
                "required": ["path", "start_line", "end_line", "new_code"]
            }
        }
    },
    "insert_code": {
        "type": "function",
        "function": {
            "name": "insert_code",
            "description": "Insert NEW code into an existing file WITHOUT replacing anything. Use read_file first to see line numbers, then set position to the line number to insert AFTER. Example: position='3' inserts your code after line 3. position='0' inserts before line 1. position='top' or 'bottom' for start/end of file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file (e.g. workspace/app.py)"},
                    "position": {"type": "string", "description": "Line number to insert AFTER (e.g. '3'), or 'top'/'bottom'"},
                    "code": {"type": "string", "description": "The new code to insert (will NOT replace existing code)"}
                },
                "required": ["path", "position", "code"]
            }
        }
    },
    "list_files": {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories recursively (up to depth 3).",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to list (default: workspace/)"}
                },
                "required": []
            }
        }
    },
    "search_code": {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search for a text pattern in source code files using grep.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Text pattern to search for"},
                    "directory": {"type": "string", "description": "Directory to search in (default: workspace/)"}
                },
                "required": ["pattern"]
            }
        }
    },
    "run_command": {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command. Already runs from the workspace/ directory by default, so do NOT add 'cd workspace' to your command. Just use filenames directly: 'python3 app.py'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute (runs from workspace/ dir, no need to cd)"},
                    "cwd": {"type": "string", "description": "Working directory (default: workspace/)"}
                },
                "required": ["command"]
            }
        }
    },
    "web_search": {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information. Returns top results with titles, URLs, and snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    "read_url": {
        "type": "function",
        "function": {
            "name": "read_url",
            "description": "Fetch and read the text content of a web page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"}
                },
                "required": ["url"]
            }
        }
    },
    "write_plan": {
        "type": "function",
        "function": {
            "name": "write_plan",
            "description": "Write a plan, architecture doc, or notes to the shared workspace for other agents to see.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Filename to write in the workspace (e.g. 'architecture.md')"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["filename", "content"]
            }
        }
    },
    "read_workspace": {
        "type": "function",
        "function": {
            "name": "read_workspace",
            "description": "Read a file from the shared workspace, or list all workspace files if no filename given.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "File to read from workspace (empty = list all files)"}
                },
                "required": []
            }
        }
    },
}


# Map of tool name → function
TOOL_FUNCTIONS = {
    "read_file": read_file,
    "write_file": write_file,
    "delete_file": delete_file,
    "edit_file": edit_file,
    "edit_lines": edit_lines,
    "insert_code": insert_code,
    "list_files": list_files,
    "search_code": search_code,
    "run_command": run_command,
    "web_search": web_search,
    "read_url": read_url,
    "write_plan": write_plan,
    "read_workspace": read_workspace,
}
