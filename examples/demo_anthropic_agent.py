"""demo_anthropic_agent.py — Anthropic agent with AgentLens auto_instrument().

Demonstrates the auto_instrument() approach — zero code changes to agent logic,
just call auto_instrument() once at startup.
Works with simulated responses if ANTHROPIC_API_KEY is not set.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sdk-python', 'src'))

from agentlens_sdk import init, auto_instrument


async def call_anthropic(question: str) -> str:
    """Call Anthropic Claude or return a simulated response."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": question}],
        )
        return response.content[0].text
    else:
        # Simulated response
        return f"[Simulated] Regarding '{question}': This is a thoughtful response from Claude."


async def main():
    print("\n  AgentLens Anthropic Auto-Instrument Demo")
    print("  Dashboard: http://localhost:5173\n")

    # Initialize and auto-instrument — ALL Anthropic calls will be traced automatically
    init(agent_name="anthropic-demo-agent")
    auto_instrument()  # Patches anthropic client

    question = "What are the benefits of observability for AI agents?"
    print(f"  Question: {question}")
    answer = await call_anthropic(question)
    print(f"  Answer:   {answer[:200]}...\n")

    await asyncio.sleep(1)
    print("  Trace sent to AgentLens. Check http://localhost:5173")


if __name__ == "__main__":
    asyncio.run(main())
