# from langgraph.graph import StateGraph

# graph = StateGraph()

# # from langchain_core.runnables import Graph
# # define nodes, edges, etc.

# from langchain_core.messages import HumanMessage
# from langchain_google_genai import ChatGoogleGenerativeAI
# from typing import TypedDict, Annotated, Sequence
# from datetime import datetime, timedelta
# import requests
# import json
# import os
# import logging

# # Configuration
# BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
# CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")
# logging.basicConfig(level=logging.INFO)

# class AgentState(TypedDict):
#     messages: Annotated[Sequence[HumanMessage], lambda x, y: x + y]
#     user_intent: str
#     appointment_details: dict

# def create_appointment_agent():
#     llm = ChatGoogleGenerativeAI(model="gemini-pro")

#     def parse_intent(state: AgentState):
#         last_message = state["messages"][-1].content
#         response = llm.invoke(f"""Analyze: "{last_message}"\nRespond with: book_appointment|check_availability|cancel_appointment|general_query""")
#         return {"user_intent": response.content.strip()}

#     def handle_booking(state: AgentState):
#         try:
#             last_message = state["messages"][-1].content
#             response = llm.invoke(f"""Extract from: "{last_message}"\nReturn JSON with: summary, duration (minutes), date (YYYY-MM-DD), time (HH:MM), attendee_email""")
#             details = json.loads(response.content)
#             details.setdefault("attendee_email", "user@example.com")
            
#             start_time = datetime.strptime(f"{details['date']} {details['time']}", "%Y-%m-%d %H:%M")
#             end_time = start_time + timedelta(minutes=details["duration"])
            
#             # Check availability
#             available = requests.get(
#                 f"{BACKEND_URL}/check_availability",
#                 params={"start_time": start_time.isoformat(), "end_time": end_time.isoformat()}
#             ).json().get("available", False)
            
#             if available:
#                 booking = requests.post(
#                     f"{BACKEND_URL}/create_event",
#                     json={
#                         "start_time": start_time.isoformat(),
#                         "end_time": end_time.isoformat(),
#                         "summary": details["summary"],
#                         "attendee_email": details["attendee_email"]
#                     }
#                 ).json()
#                 return {
#                     "messages": [HumanMessage(content=f"✅ Booked! Join: {booking.get('meet_link', '')}")],
#                     "appointment_details": details
#                 }
#             else:
#                 new_time = start_time + timedelta(hours=1)
#                 return {
#                     "messages": [HumanMessage(content=f"⏳ Slot taken. Try {new_time.strftime('%Y-%m-%d %H:%M')}?")],
#                     "appointment_details": details
#                 }
#         except Exception as e:
#             logging.error(f"Booking error: {str(e)}")
#             return {
#                 "messages": [HumanMessage(content="⚠️ Error processing request. Please try again.")],
#                 "appointment_details": {}
#             }

#     # Build workflow
#     workflow = StateGraph()
#     workflow.add_node("parse_intent", parse_intent)
#     workflow.add_node("book_appointment", handle_booking)
#     workflow.add_edge("parse_intent", "book_appointment")
#     workflow.set_entry_point("parse_intent")
    
#     return workflow.compile()

# appointment_agent = create_appointment_agent()




















# agent.py

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor
from langchain.tools.google_calendar import (
    GoogleCalendarCreateEvent,
    GoogleCalendarSearchEvents,
)
from langgraph.graph import StateGraph, END
from langgraph.graph.schema import RunnableConfig
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
    return await llm.agenerate(messages=state)

@node
async def run_tools(state):
    return await tools[0].ainvoke(state)  # or use dynamic tool selection if needed

# 4. Build the LangGraph
def build_agent():
    builder = StateGraph()
    builder.add_node("LLM", call_llm)
    builder.add_node("TOOLS", run_tools)

    builder.set_entry_point("LLM")
    builder.add_edge("LLM", "TOOLS")
    builder.add_edge("TOOLS", "LLM")
    builder.add_edge("LLM", END)

    graph = builder.compile()
    return graph

# 5. Export the compiled agent
appointment_agent = build_agent()
