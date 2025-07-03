# # main.py
# from fastapi import FastAPI
# from pydantic import BaseModel
# from datetime import datetime
# from google.oauth2 import service_account
# from googleapiclient.discovery import build
# import uuid
# import logging
# logging.basicConfig(level=logging.INFO)  # એરર્સ ડીબગ કરવા માટે

# app = FastAPI()

# # Load service account credentials
# SCOPES = ['https://www.googleapis.com/auth/calendar']
# SERVICE_ACCOUNT_FILE = 'service_account.json'

# credentials = service_account.Credentials.from_service_account_file(
#     SERVICE_ACCOUNT_FILE, scopes=SCOPES)
# calendar_service = build('calendar', 'v3', credentials=credentials)

# class AppointmentRequest(BaseModel):
#     start_time: str
#     end_time: str
#     summary: str
#     attendee_email: str
#     timeZone='Asia/Kolkata'

# @app.post("/create_event")
# async def create_event(request: AppointmentRequest):
#     event = {
#         'summary': request.summary,
#         'start': {
#             'dateTime': request.start_time,
#             'timeZone': 'UTC',
#         },
#         'end': {
#             'dateTime': request.end_time,
#             'timeZone': 'UTC',
#         },
#         'attendees': [{'email': request.attendee_email}],
#         'conferenceData': {
#             'createRequest': {
#                 'requestId': str(uuid.uuid4()),
#                 'conferenceSolutionKey': {'type': 'hangoutsMeet'}
#             }
#         },
#     }
    
#     event = calendar_service.events().insert(
#         calendarId='9d23676d1e15e9140e9cc944f3ff3355740f76401fa468835d8107fd4a96817d@group.calendar.google.com',
#         body=event,
#         conferenceDataVersion=1
#     ).execute()
    
#     return {"event_id": event['id'], "meet_link": event['hangoutLink']}

# @app.get("/check_availability")
# async def check_availability(start_time: str, end_time: str):
#     # Check for existing events in the time range
#     events_result = calendar_service.events().list(
#         calendarId='9d23676d1e15e9140e9cc944f3ff3355740f76401fa468835d8107fd4a96817d@group.calendar.google.com',
#         timeMin=start_time,
#         timeMax=end_time,
#         singleEvents=True,
#         orderBy='startTime'
#     ).execute()
    
#     events = events_result.get('items', [])
#     return {"available": len(events) == 0}







from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from fastapi.middleware.cors import CORSMiddleware
import uuid
import logging
import os

# Initialize logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Calendar configuration
CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

# Load service account credentials
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'service_account.json'

try:
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    calendar_service = build('calendar', 'v3', credentials=credentials)
except Exception as e:
    logging.error(f"Failed to initialize calendar service: {str(e)}")
    raise

class AppointmentRequest(BaseModel):
    start_time: str
    end_time: str
    summary: str
    attendee_email: str

@app.post("/create_event")
async def create_event(request: AppointmentRequest):
    try:
        event = {
            'summary': request.summary,
            'start': {
                'dateTime': request.start_time,
                'Asia/Kolkata': TIMEZONE,
            },
            'end': {
                'dateTime': request.end_time,
                'Asia/Kolkata': TIMEZONE,
            },
            'attendees': [{'email': request.attendee_email}],
            'conferenceData': {
                'createRequest': {
                    'requestId': str(uuid.uuid4()),
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            },
        }
        
        event = calendar_service.events().insert(
            calendarId='9d23676d1e15e9140e9cc944f3ff3355740f76401fa468835d8107fd4a96817d@group.calendar.google.com',
            body=event,
            conferenceDataVersion=1
        ).execute()
        
        return {"event_id": event['id'], "meet_link": event['hangoutLink']}
    except Exception as e:
        logging.error(f"Error creating event: {str(e)}")
        return {"error": str(e)}

@app.get("/check_availability")
async def check_availability(start_time: str, end_time: str):
    try:
        events_result = calendar_service.events().list(
            calendarId='9d23676d1e15e9140e9cc944f3ff3355740f76401fa468835d8107fd4a96817d@group.calendar.google.com',
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return {"available": len(events) == 0}
    except Exception as e:
        logging.error(f"Error checking availability: {str(e)}")
        return {"error": str(e)}

@app.get("/")
async def health_check():
    return {"status": "healthy"}