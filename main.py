from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import uuid
import logging

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Google Calendar Setup
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'service_account.json'
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)

class EventRequest(BaseModel):
    start_time: str
    end_time: str
    summary: str
    attendee_email: str

@app.post("/create_event")
def create_event(request: EventRequest):
    try:
        event = {
            'summary': request.summary,
            'start': {'dateTime': request.start_time, 'timeZone': 'Asia/Kolkata'},
            'end': {'dateTime': request.end_time, 'timeZone': 'Asia/Kolkata'},
            'attendees': [{'email': request.attendee_email}],
            'conferenceData': {
                'createRequest': {
                    'requestId': str(uuid.uuid4()),
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }
        }
        
        event = service.events().insert(
            calendarId=os.getenv("CALENDAR_ID"),
            body=event,
            conferenceDataVersion=1
        ).execute()
        
        return {
            "status": "success",
            "event_id": event['id'],
            "meet_link": event['hangoutLink']
        }
    except Exception as e:
        logging.error(f"Event creation failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/check_availability")
def check_availability(start_time: str, end_time: str):
    try:
        events = service.events().list(
            calendarId=os.getenv("CALENDAR_ID"),
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute().get('items', [])
        
        return {"available": len(events) == 0}
    except Exception as e:
        logging.error(f"Availability check failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "calendar-booking-api"}