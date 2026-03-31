"""
Base Agent class.
Each agent has a name, a role (system prompt), and a set of tools it can use.

SPEED OPTIMIZATION — KV Cache Prefix Sharing:
  All agents share a common system-prompt prefix (from config.SHARED_SYSTEM_PREFIX).
  This means when LM Studio processes Agent B after Agent A, it can reuse the
  KV cache for the shared prefix tokens instead of recomputing them from scratch.
  On a 7B model, this saves ~200-500ms per agent switch.
"""

from rich.console import Console
import llm
import config
import tools as tool_module

console = Console()


class Agent:
    """A single AI agent with a specific role and tool set."""

    def __init__(self, name: str, role: str, tool_names: list[str]):
        """
        Args:
            name: Display name (e.g. "Architect")
            role: System prompt describing the agent's persona and job
            tool_names: List of tool names this agent can use (from tools.py)
        """
        self.name = name
        # KV Cache optimization: prepend shared prefix so all agents
        # share the same token prefix → LM Studio reuses KV cache
        self.role = f"{config.SHARED_SYSTEM_PREFIX}\n\n{role}"
        self.tool_names = tool_names

        # Build the tool schemas and function map for this agent
        self.tool_schemas = [
            tool_module.TOOL_SCHEMAS[t] for t in tool_names
            if t in tool_module.TOOL_SCHEMAS
        ]
        self.tool_functions = {
            t: tool_module.TOOL_FUNCTIONS[t] for t in tool_names
            if t in tool_module.TOOL_FUNCTIONS
        }

    def run(self, task: str, context: str = "") -> str:
        """
        Run this agent on a task.

        Args:
            task: What the agent should do
            context: Additional context from previous agents or the workspace

        Returns:
            The agent's final text response
        """
        console.print(f"  [bold]{self.name}[/bold]")

        system_msg = self.role
        if context:
            system_msg += f"\n\n--- CONTEXT FROM PREVIOUS WORK ---\n{context}"

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": task},
        ]

        # Speed: agents with tools use a smaller token limit than the default 8K
        # Code agents use lower temperature for more reliable tool calling
        response = llm.chat(
            messages=messages,
            tools=self.tool_schemas if self.tool_schemas else None,
            tool_functions=self.tool_functions,
            agent_name=self.name,
            max_tokens=config.MAX_TOKENS_TOOL_AGENT,
            temperature=config.TEMPERATURE_CODE if self.tool_schemas else None,
        )

        console.print()


        return response
