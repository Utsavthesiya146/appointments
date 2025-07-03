# agent.py

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor
from langchain.tools.google_calendar import (
    GoogleCalendarCreateEvent,
    GoogleCalendarSearchEvents,
)
from langgraph.graph import StateGraph, END
from langgraph.graph import node

# 1. Setup LLM
llm = ChatGoogleGenerativeAI(
    model=os.getenv("MODEL_NAME", "gemini-1.5-flash"),
    temperature=0.3,
)

# 2. Setup tools
tools = [
    GoogleCalendarCreateEvent(calendar_id=os.getenv("DEFAULT_CALENDAR_ID", "primary")),
    GoogleCalendarSearchEvents(calendar_id=os.getenv("DEFAULT_CALENDAR_ID", "primary")),
]

# 3. Define LangGraph nodes
@node
async def call_llm(state):
    return await llm.ainvoke(state)

@node
async def run_tools(state):
    # This example doesn't dynamically choose tools; update this logic if needed
    return await tools[0].ainvoke(state)

# 4. Build LangGraph and compile
def build_agent():
    builder = StateGraph()
    builder.add_node("LLM", call_llm)
    builder.add_node("TOOLS", run_tools)

    builder.set_entry_point("LLM")
    builder.add_edge("LLM", "TOOLS")
    builder.add_edge("TOOLS", "LLM")
    builder.add_edge("LLM", END)

    return builder.compile()

# 5. Create the global agent
appointment_agent = build_agent()