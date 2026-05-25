"""
Conversation Agent for the Islamabad/Rawalpindi Food & Picnic Guide.

Uses Groq's API (free tier) with tool calling for intelligent, multi-turn conversations.
Get a free API key at: https://console.groq.com

The agent automatically handles tool calls in a loop until a final text response is produced.
"""

import json
import os
from typing import List, Dict

from groq import Groq

from agents.toolkit import TOOLS, execute_tool, to_groq_tools
from agents.prompt_library import SYSTEM_PROMPT, ERROR_MESSAGE


class FoodGuideAgent:
    """
    AI-powered agent for the Islamabad/Rawalpindi Food & Picnic Guide.

    Uses Groq (free API) with llama-3.3-70b-versatile by default.

    Usage:
        agent = FoodGuideAgent()
        reply = agent.chat("Suggest a good restaurant in F-7")
        agent.reset()  # clear conversation history for a new session
    """

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable is not set. "
                "Get a free key at https://console.groq.com"
            )
        self.client = Groq(api_key=api_key)
        self.model = model
        self.groq_tools = to_groq_tools(TOOLS)
        self.conversation_history: List[Dict] = []

    def reset(self) -> None:
        """Clear the conversation history to start a fresh session."""
        self.conversation_history = []

    def chat(self, user_message: str) -> str:
        """
        Send a user message and return the assistant's final text response.
        Tool calls are handled automatically in an internal loop.

        Args:
            user_message: The user's input string.

        Returns:
            The assistant's final text response as a string.
        """
        self.conversation_history.append({"role": "user", "content": user_message})

        try:
            return self._agent_loop()
        except Exception as e:
            return f"{ERROR_MESSAGE} (Details: {e})"

    def _agent_loop(self) -> str:
        """
        Internal agentic loop:
          1. Call Groq with system prompt + full conversation history.
          2. If finish_reason == 'tool_calls', execute each tool and append
             the results, then loop back to step 1.
          3. When finish_reason == 'stop', return the final text response.
        """
        # Build the full message list for this turn (system + history)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + list(
            self.conversation_history
        )

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.groq_tools,
                tool_choice="auto",
                max_tokens=4096,
                temperature=0,      # keeps tool calls deterministic and well-formed
            )

            choice = response.choices[0]
            message = choice.message
            finish_reason = choice.finish_reason

            # Serialize the assistant message so it can be stored in history
            assistant_msg: Dict = {"role": "assistant", "content": message.content or ""}
            if message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ]
            messages.append(assistant_msg)

            if finish_reason == "stop":
                # Persist this full exchange into conversation history
                self.conversation_history = [
                    m for m in messages if m["role"] != "system"
                ]
                return message.content or ""

            if finish_reason == "tool_calls":
                # Execute every tool the model requested
                for tool_call in (message.tool_calls or []):
                    try:
                        args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        args = {}

                    result = execute_tool(tool_call.function.name, args)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                    )
                # Continue the loop so the model can respond to the tool results

            else:
                # Unexpected finish reason — return a safe fallback
                return ERROR_MESSAGE
