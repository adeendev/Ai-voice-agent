"""
Google Calendar Integration Module
Handles Google Calendar API operations for appointment booking.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# ===== TIMEZONE CONFIGURATION =====
# Should match the timezone used in the voice agent
LOCAL_TIMEZONE = 'America/New_York'  # Eastern Time
TIMEZONE_OBJ = pytz.timezone(LOCAL_TIMEZONE)

class GoogleCalendarIntegration:
    """Google Calendar API integration for booking appointments."""
    
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.json"):
        """Initialize Google Calendar integration."""
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        self.authenticated = False
        
        try:
            self.authenticate()
            logger.info("Google Calendar integration initialized successfully")
        except Exception as e:
            logger.warning(f"Google Calendar authentication failed: {e}")
            logger.info("Google Calendar integration will be disabled. Server will continue without calendar features.")
            # Don't raise the exception - allow server to continue
    
    def authenticate(self):
        """Authenticate with Google Calendar API."""
        creds = None
        
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Google Calendar credentials refreshed")
                except Exception as e:
                    logger.warning(f"Failed to refresh credentials: {e}")
                    logger.info("Google Calendar will be disabled. Please re-authenticate manually if needed.")
                    self.authenticated = False
                    return False
            
            if not creds:
                logger.warning("No valid Google Calendar credentials found.")
                logger.info("Google Calendar integration disabled. Server will continue without calendar features.")
                self.authenticated = False
                return False
            
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            self.authenticated = True
            logger.info("Google Calendar service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to build Google Calendar service: {e}")
            self.authenticated = False
            return False
    
    def create_appointment(self, 
                          title: str,
                          description: str, 
                          start_time: datetime, 
                          duration_minutes: int = 60,
                          attendee_email: str = None) -> Dict[str, Any]:
        """
        Create an appointment in Google Calendar.
        
        Args:
            title: Event title
            description: Event description
            start_time: Date and time of appointment
            duration_minutes: Duration in minutes (default 60)
            attendee_email: Attendee email address
            
        Returns:
            Dict with 'success' boolean and 'event_id' or 'error'
        """
        if not self.service or not self.authenticated:
            logger.warning("Google Calendar service not available - integration disabled")
            return {'success': False, 'error': 'Google Calendar service not available'}
        
        try:
            # Ensure start_time is timezone-aware
            if start_time.tzinfo is None:
                logger.warning("start_time is not timezone-aware, assuming local timezone")
                start_time = TIMEZONE_OBJ.localize(start_time)
            
            # Calculate end time
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            logger.info(f"Creating calendar event: {title}")
            logger.info(f"Start time: {start_time} ({start_time.tzinfo})")
            logger.info(f"End time: {end_time} ({end_time.tzinfo})")
            
            # Create attendees list if email provided
            attendees = []
            if attendee_email:
                attendees.append({'email': attendee_email})
            
            # Create event - use the timezone from the datetime object
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': str(start_time.tzinfo),
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': str(end_time.tzinfo),
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 30},       # 30 minutes before
                    ],
                },
            }
            
            # Add attendees if provided
            if attendees:
                event['attendees'] = attendees
            
            # Insert event
            event_result = self.service.events().insert(
                calendarId=self.calendar_id, 
                body=event
            ).execute()
            
            event_id = event_result.get('id')
            logger.info(f"Google Calendar event created successfully: {event_id}")
            return {'success': True, 'event_id': event_id}
            
        except HttpError as error:
            logger.error(f"Google Calendar API error: {error}")
            return {'success': False, 'error': str(error)}
        except Exception as e:
            logger.error(f"Failed to create Google Calendar event: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_appointment(self, event_id: str, **kwargs) -> bool:
        """
        Update an existing appointment in Google Calendar.
        
        Args:
            event_id: Google Calendar event ID
            **kwargs: Fields to update
            
        Returns:
            True if successful, False if failed
        """
        if not self.service:
            logger.error("Google Calendar service not initialized")
            return False
        
        try:
            # Get existing event
            event = self.service.events().get(
                calendarId=self.calendar_id, 
                eventId=event_id
            ).execute()
            
            # Update fields
            if 'customer_name' in kwargs or 'service_name' in kwargs:
                customer_name = kwargs.get('customer_name', 'Customer')
                service_name = kwargs.get('service_name', 'Service')
                event['summary'] = f"{service_name} - {customer_name}"
            
            if 'appointment_datetime' in kwargs:
                appointment_datetime = kwargs['appointment_datetime']
                duration_minutes = kwargs.get('duration_minutes', 60)
                end_time = appointment_datetime + timedelta(minutes=duration_minutes)
                
                event['start']['dateTime'] = appointment_datetime.isoformat()
                event['end']['dateTime'] = end_time.isoformat()
            
            # Update event
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"Google Calendar event updated successfully: {event_id}")
            return True
            
        except HttpError as error:
            logger.error(f"Google Calendar API error: {error}")
            return False
        except Exception as e:
            logger.error(f"Failed to update Google Calendar event: {e}")
            return False
    
    def delete_appointment(self, event_id: str) -> bool:
        """
        Delete an appointment from Google Calendar.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if successful, False if failed
        """
        if not self.service:
            logger.error("Google Calendar service not initialized")
            return False
        
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Google Calendar event deleted successfully: {event_id}")
            return True
            
        except HttpError as error:
            logger.error(f"Google Calendar API error: {error}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete Google Calendar event: {e}")
            return False
    
    def get_appointments(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """
        Get appointments from Google Calendar.
        
        Args:
            start_date: Start date for search (default: today)
            end_date: End date for search (default: 30 days from start)
            
        Returns:
            List of appointment dictionaries
        """
        if not self.service:
            logger.error("Google Calendar service not initialized")
            return []
        
        if not start_date:
            start_date = datetime.now()
        
        if not end_date:
            end_date = start_date + timedelta(days=30)
        
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_date.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            appointments = []
            
            for event in events:
                appointment = {
                    'id': event.get('id'),
                    'summary': event.get('summary', ''),
                    'description': event.get('description', ''),
                    'start': event.get('start', {}).get('dateTime'),
                    'end': event.get('end', {}).get('dateTime'),
                    'status': event.get('status', 'confirmed')
                }
                appointments.append(appointment)
            
            logger.info(f"Retrieved {len(appointments)} appointments from Google Calendar")
            return appointments
            
        except HttpError as error:
            logger.error(f"Google Calendar API error: {error}")
            return []
        except Exception as e:
            logger.error(f"Failed to get Google Calendar appointments: {e}")
            return []
    
    def check_availability(self, appointment_datetime: datetime, duration_minutes: int = 60) -> bool:
        """
        Check if a time slot is available.
        
        Args:
            appointment_datetime: Proposed appointment time
            duration_minutes: Duration in minutes
            
        Returns:
            True if available, False if busy
        """
        if not self.service:
            logger.error("Google Calendar service not initialized")
            return False
        
        try:
            end_time = appointment_datetime + timedelta(minutes=duration_minutes)
            
            # Check for conflicts
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=appointment_datetime.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                singleEvents=True
            ).execute()
            
            events = events_result.get('items', [])
            
            # If no events found, slot is available
            available = len(events) == 0
            logger.info(f"Time slot availability check: {'Available' if available else 'Busy'}")
            return available
            
        except HttpError as error:
            logger.error(f"Google Calendar API error: {error}")
            return False
        except Exception as e:
            logger.error(f"Failed to check availability: {e}")
            return False