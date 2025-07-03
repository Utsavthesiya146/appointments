# # agent.py
# from langgraph.graph import Graph
# from langchain_core.messages import HumanMessage
# from langchain_google_genai import ChatGoogleGenerativeAI
# from typing import TypedDict, Annotated, Sequence
# from datetime import datetime, timedelta
# import requests
# import logging

# class AgentState(TypedDict):
#     messages: Annotated[Sequence[HumanMessage], lambda x, y: x + y]
#     user_intent: str
#     appointment_details: dict

# llm = ChatGoogleGenerativeAI(model="gemini-pro")

# def parse_intent(state: AgentState):
#     last_message = state["messages"][-1].content
#     response = llm.invoke(f"""
#     Analyze the following user message to determine intent:
#     Message: "{last_message}"
    
#     Possible intents:
#     - book_appointment
#     - check_availability
#     - cancel_appointment
#     - general_query
    
#     Respond ONLY with the intent name.
#     """)
    
#     return {"user_intent": response.content.strip()}

# def handle_appointment_booking(state: AgentState):
#     last_message = state["messages"][-1].content
#     response = llm.invoke(f"""
#     Extract appointment details from this message:
#     "{last_message}"
    
#     Return as JSON with these fields:
#     - summary (string): Meeting title/subject
#     - duration (number): Duration in minutes
#     - date (string): Preferred date in YYYY-MM-DD format
#     - time (string): Preferred start time in HH:MM format
#     - attendee_email (string): Attendee email if mentioned
#     """)
    
#     details = eval(response.content)
#     details["attendee_email"] = details.get("attendee_email", "user@example.com")
    
#     # Calculate end time
#     start_time = datetime.strptime(f"{details['date']} {details['time']}", "%Y-%m-%d %H:%M")
#     end_time = start_time + timedelta(minutes=details["duration"])
    
#     # Check availability
#     availability = requests.get(
#         "http://localhost:8000/check_availability",
#         params={
#             "start_time": start_time.isoformat(),
#             "end_time": end_time.isoformat()
#         }
#     ).json()
    
#     if availability["available"]:
#         # Book appointment
#         booking = requests.post(
#             "http://localhost:8000/create_event",
#             json={
#                 "start_time": start_time.isoformat(),
#                 "end_time": end_time.isoformat(),
#                 "summary": details["summary"],
#                 "attendee_email": details["attendee_email"]
#             }
#         ).json()
        
#         return {
#             "messages": [HumanMessage(
#                 content=f"Appointment booked! Meet link: {booking['meet_link']}"
#             )],
#             "appointment_details": details
#         }
#     else:
#         # Suggest alternatives
#         new_time = start_time + timedelta(hours=1)
#         return {
#             "messages": [HumanMessage(
#                 content=f"Sorry, that slot is booked. How about {new_time.strftime('%Y-%m-%d %H:%M')}?"
#             )],
#             "appointment_details": details
#         }

# workflow = Graph()

# workflow.add_node("parse_intent", parse_intent)
# workflow.add_node("book_appointment", handle_appointment_booking)

# workflow.add_edge("parse_intent", "book_appointment")

# workflow.set_entry_point("parse_intent")
# appointment_agent = workflow.compile()




from langchain_core.runnables.graph import Graph
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Annotated, Sequence
from datetime import datetime, timedelta
import requests
import json
import os
import logging

# Configure backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

class AgentState(TypedDict):
    messages: Annotated[Sequence[HumanMessage], lambda x, y: x + y]
    user_intent: str
    appointment_details: dict

llm = ChatGoogleGenerativeAI(model="gemini-pro")

def parse_intent(state: AgentState):
    last_message = state["messages"][-1].content
    response = llm.invoke(f"""
    Analyze the following user message to determine intent:
    Message: "{last_message}"
    
    Possible intents:
    - book_appointment
    - check_availability
    - cancel_appointment
    - general_query
    
    Respond ONLY with the intent name.
    """)
    
    return {"user_intent": response.content.strip()}

def handle_appointment_booking(state: AgentState):
    last_message = state["messages"][-1].content
    response = llm.invoke(f"""
    Extract appointment details from this message:
    "{last_message}"
    
    Return as JSON with these fields:
    - summary (string): Meeting title/subject
    - duration (number): Duration in minutes
    - date (string): Preferred date in YYYY-MM-DD format
    - time (string): Preferred start time in HH:MM format
    - attendee_email (string): Attendee email if mentioned
    """)
    
    try:
        details = json.loads(response.content)
        details["attendee_email"] = details.get("attendee_email", "user@example.com")
        
        # Calculate end time
        start_time = datetime.strptime(f"{details['date']} {details['time']}", "%Y-%m-%d %H:%M")
        end_time = start_time + timedelta(minutes=details["duration"])
        
        # Check availability
        availability = requests.get(
            f"{BACKEND_URL}/check_availability",
            params={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
        ).json()
        
        if availability["available"]:
            # Book appointment
            booking = requests.post(
                f"{BACKEND_URL}/create_event",
                json={
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "summary": details["summary"],
                    "attendee_email": details["attendee_email"]
                }
            ).json()
            
            return {
                "messages": [HumanMessage(
                    content=f"Appointment booked! Meet link: {booking['meet_link']}"
                )],
                "appointment_details": details
            }
        else:
            # Suggest alternatives
            new_time = start_time + timedelta(hours=1)
            return {
                "messages": [HumanMessage(
                    content=f"Sorry, that slot is booked. How about {new_time.strftime('%Y-%m-%d %H:%M')}?"
                )],
                "appointment_details": details
            }
    except Exception as e:
        logging.error(f"Error in booking: {str(e)}")
        return {
            "messages": [HumanMessage(
                content="Sorry, I encountered an error processing your request. Please try again."
            )],
            "appointment_details": {}
        }

workflow = Graph()
# Add nodes with proper data formatting
workflow.add_node(
    "parse_intent",
    {
        "runnable": parse_intent,
        "name": "Parse Intent"
    }
)

workflow.add_node(
    "book_appointment",
    {
        "runnable": handle_appointment_booking,
        "name": "Book Appointment"
    }
)

# Set entry point
workflow.set_entry_point("parse_intent")

# Compile the workflow
appointment_agent = workflow.compile()

workflow.add_node("parse_intent", parse_intent)
workflow.add_node("book_appointment", handle_appointment_booking)
workflow.add_edge("parse_intent", "book_appointment")
workflow.set_entry_point("parse_intent")
appointment_agent = workflow.compile()
# At the end of agent.py
__all__ = ['appointment_agent']  # Explicitly expose the agent