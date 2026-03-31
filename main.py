#!/usr/bin/env python3
"""
Entry point for the Multi-Agent System.

Usage:
  python main.py                  → interactive REPL
  python main.py "your task"      → one-shot mode
"""

import sys
from rich.console import Console

import config
from orchestrator import run_task, maybe_clean_workspace

console = Console()


def _header():
    from llm import get_model
    model = get_model()
    console.print()
    console.print("  [bold white]╻ ╻╻ ╻╻ ╻[/bold white]")
    console.print("  [bold white]┃┗┫┃┗┫┃┗┫[/bold white]")
    console.print("  [bold white]╹ ╹╹ ╹╹ ╹[/bold white]")
    console.print(f"  [dim]{config.LM_BASE_URL} · {model}[/dim]")
    console.print()


def _repl():
    """Interactive REPL — keep accepting tasks until the user exits."""
    _header()
    maybe_clean_workspace()
    console.print("  [dim]type a task, or 'exit' to quit[/dim]")
    console.print()

    while True:
        try:
            task = console.input("  [bold]>[/bold] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print()
            console.print("  [dim]bye[/dim]")
            break

        if not task:
            continue
        if task.lower() in ("exit", "quit", "q"):
            console.print("  [dim]bye[/dim]")
            break

        try:
            run_task(task)
        except KeyboardInterrupt:
            console.print()
            console.print("  [dim]cancelled[/dim]")
            console.print()
        except Exception as e:
            console.print(f"  [red]error:[/red] {e}")
            console.print()


def _one_shot(task: str):
    """Run a single task and exit."""
    _header()
    maybe_clean_workspace()
    try:
        run_task(task)
    except KeyboardInterrupt:
        console.print()
        console.print("  [dim]cancelled[/dim]")
        sys.exit(1)
    except Exception as e:
        console.print(f"  [red]error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    if len(sys.argv) >= 2:
        # One-shot: python main.py "build me a flask app"
        _one_shot(" ".join(sys.argv[1:]))
    else:
        # Interactive REPL
        _repl()


if __name__ == "__main__":
    main()
