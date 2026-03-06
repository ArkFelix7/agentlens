"""demo_openai_agent.py — Minimal OpenAI agent with AgentLens @trace decorator.

Demonstrates the simplest possible integration — just two lines added to any agent.
Works with simulated responses if OPENAI_API_KEY is not set.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sdk-python', 'src'))

from agentlens_sdk import init, trace


async def call_openai(question: str) -> str:
    """Call OpenAI or return a simulated response."""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        import openai
        client = openai.AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": question}],
        )
        return response.choices[0].message.content
    else:
        # Simulated response
        return f"[Simulated] The answer to '{question}' is 42."


@trace(name="answer_question", event_type="llm_call")
async def answer_question(question: str) -> str:
    """Ask a question and return the answer."""
    return await call_openai(question)


async def main():
    print("\n  AgentLens Simple OpenAI Agent Demo")
    print("  Dashboard: http://localhost:5173\n")

    # Initialize AgentLens — just this one line!
    init(agent_name="openai-demo-agent")

    # Run the traced function
    question = "What is the capital of France?"
    print(f"  Question: {question}")
    answer = await answer_question(question)
    print(f"  Answer:   {answer}\n")

    await asyncio.sleep(1)  # Give SDK time to flush
    print("  Trace sent to AgentLens. Check http://localhost:5173")


if __name__ == "__main__":
    asyncio.run(main())
