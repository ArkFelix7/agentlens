"""demo_langchain_agent.py — LangChain agent with AgentLens callback handler.

Shows how to use the AgentLensCallbackHandler with any LangChain chain.
Works with simulated responses if OPENAI_API_KEY is not set.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sdk-python', 'src'))

from agentlens import init


async def main():
    print("\n  AgentLens LangChain Callback Demo")
    print("  Dashboard: http://localhost:5173\n")

    init(agent_name="langchain-demo-agent")

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from agentlens.interceptors.langchain_interceptor import AgentLensCallbackHandler

        handler = AgentLensCallbackHandler()
        llm = ChatOpenAI(model="gpt-4o-mini", callbacks=[handler])
        prompt = ChatPromptTemplate.from_messages([
            ("human", "{question}")
        ])
        chain = prompt | llm

        result = await chain.ainvoke(
            {"question": "Explain LangChain in one sentence."},
            config={"callbacks": [handler]},
        )
        print(f"  Result: {result.content}")
    except ImportError:
        print("  LangChain not installed. Sending simulated trace instead.")
        from agentlens.trace import SpanContext, get_client, get_session_id
        span = SpanContext("tool_call", "langchain_simulated", get_session_id() or "demo", get_client())
        span.set_input({"question": "Explain LangChain in one sentence."})
        span.set_output({"answer": "LangChain is a framework for building LLM-powered applications."})
        span.end()
        await asyncio.sleep(1)

    print("\n  Trace sent to AgentLens. Check http://localhost:5173")


if __name__ == "__main__":
    asyncio.run(main())
