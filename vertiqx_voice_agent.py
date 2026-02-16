"""
Vertiqx Professional Receptionist Agent - Fixed & Enhanced
==========================================================
Natural conversational AI with proper service detection and flow.
"""

import google.generativeai as genai
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import json
import logging
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import re
import dateparser
from dateutil import parser as dateutil_parser
import pytz
from booking_database import BookingDatabase
from booking_manager import BookingManager

# ===== LOGGING SETUP =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vertiqx_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===== TIMEZONE CONFIGURATION =====
# Default to Eastern Time (most common US business timezone)
# This can be configured based on business location
LOCAL_TIMEZONE = 'America/New_York'  # Eastern Time
TIMEZONE_OBJ = pytz.timezone(LOCAL_TIMEZONE)

# ===== GOOGLE CALENDAR CONFIG =====
SCOPES = ['https://www.googleapis.com/auth/calendar']

# ===== SERVICE CATALOG =====
SERVICES_CATALOG = {
    "AI Calling Agents": {
        "name": "AI Calling Agents",
        "description": (
            "Our AI calling agents handle your business calls 24/7 — they can talk naturally, "
            "book appointments, answer FAQs, and make sure you never miss a single lead."
        ),
        "pricing": {
            "starter": {
                "price": "$299/month",
                "calls": "Up to 500 calls/month",
                "features": [
                    "Handles basic inquiries and bookings",
                    "Call recordings included",
                    "Available 24/7"
                ]
            },
            "professional": {
                "price": "$599/month",
                "calls": "Up to 1,500 calls/month",
                "features": [
                    "Smarter AI trained for your business tone",
                    "Custom voice setup",
                    "CRM integration",
                    "Priority support"
                ]
            },
            "enterprise": {
                "price": "Custom pricing",
                "calls": "Unlimited calls",
                "features": [
                    "Dedicated account manager",
                    "Custom integrations",
                    "White-label option",
                    "24/7 premium support"
                ]
            },
        },
        "benefits": [
            "Never miss a customer call again",
            "Available around the clock",
            "Reduce staff workload",
            "Deliver a professional and friendly experience"
        ]
    },

    "WhatsApp Business Automation": {
        "name": "WhatsApp Business Automation",
        "description": (
            "Let your WhatsApp handle itself — automate replies, manage orders, "
            "send promotions, and provide instant customer support with ease."
        ),
        "pricing": {
            "starter": {
                "price": "$199/month",
                "messages": "Up to 5,000 messages/month",
                "features": [
                    "Auto-replies and basic chatbot",
                    "Broadcast messaging",
                    "Message templates included"
                ]
            },
            "professional": {
                "price": "$449/month",
                "messages": "Up to 15,000 messages/month",
                "features": [
                    "Smart AI chatbot that learns from conversations",
                    "Order and payment management",
                    "Analytics dashboard",
                    "Advanced workflows"
                ]
            },
            "enterprise": {
                "price": "Custom pricing",
                "messages": "Unlimited messages",
                "features": [
                    "Multi-agent setup",
                    "Custom automation flows",
                    "API access",
                    "Dedicated support"
                ]
            },
        },
        "benefits": [
            "Instant replies to customers",
            "Automate FAQs and updates",
            "Boost engagement and conversions",
            "Provide faster support without extra staff"
        ]
    },

    "Booking Systems": {
        "name": "Booking Systems",
        "description": (
            "Simplify how customers book with you. Manage appointments, send reminders, "
            "and keep everything organized — all in one clean dashboard."
        ),
        "pricing": {
            "starter": {
                "price": "$149/month",
                "bookings": "Up to 200 bookings/month",
                "features": [
                    "Online booking widget",
                    "Calendar sync",
                    "Email confirmations"
                ]
            },
            "professional": {
                "price": "$299/month",
                "bookings": "Up to 1,000 bookings/month",
                "features": [
                    "Custom branding",
                    "SMS reminders",
                    "Payment integration",
                    "Analytics dashboard"
                ]
            },
            "enterprise": {
                "price": "Custom pricing",
                "bookings": "Unlimited bookings",
                "features": [
                    "Multi-location support",
                    "API access",
                    "White-label setup",
                    "Priority support"
                ]
            },
        },
        "benefits": [
            "Reduce no-shows automatically",
            "Let customers book anytime",
            "Save time with automated scheduling",
            "Stay organized and professional"
        ]
    },

    "Admin Dashboards": {
        "name": "Admin Dashboards",
        "description": (
            "Stay on top of everything that matters — track performance, monitor sales, "
            "and get real-time insights from a powerful and easy-to-use dashboard."
        ),
        "pricing": {
            "starter": {
                "price": "$249/month",
                "users": "Up to 5 users",
                "features": [
                    "Real-time analytics",
                    "Basic performance reports",
                    "Mobile-friendly access"
                ]
            },
            "professional": {
                "price": "$499/month",
                "users": "Up to 20 users",
                "features": [
                    "Custom analytics and reporting",
                    "Team management tools",
                    "Data export options",
                    "Advanced filters and KPIs"
                ]
            },
            "enterprise": {
                "price": "Custom pricing",
                "users": "Unlimited users",
                "features": [
                    "Fully custom dashboards",
                    "API access and integrations",
                    "White-label setup",
                    "Dedicated account manager"
                ]
            },
        },
        "benefits": [
            "Make smarter, data-driven decisions",
            "Get real-time visibility across teams",
            "Encourage collaboration with shared dashboards",
            "Track growth and performance easily"
        ]
    }
}


# ===== CONVERSATION STATE =====
class ConversationState:
    """Conversation states for the booking flow."""
    GREETING = "greeting"
    EXPLORING_SERVICES = "exploring_services"
    SERVICE_SELECTED = "service_selected"
    COLLECTING_NAME = "collecting_name"
    CONFIRMING_NAME = "confirming_name"
    COLLECTING_DATE = "collecting_date"
    CONFIRMING_DATE = "confirming_date"
    COLLECTING_TIME = "collecting_time"
    FINAL_CONFIRMATION = "final_confirmation"
    COMPLETED = "completed"

# ===== BOOKING CONTEXT =====
@dataclass
class BookingContext:
    """Booking context with clear state management."""
    name: str = ""
    service: str = ""
    date: str = ""
    time: str = ""
    booking_id: str = ""
    notes: str = ""
    
    # State tracking
    state: str = ConversationState.GREETING
    name_confirmed: bool = False
    service_confirmed: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)

# ===== CALENDAR SERVICE =====
class CalendarService:
    """Google Calendar integration."""
    
    def __init__(self):
        self.service = None
        self._initialize_calendar()
    
    def _initialize_calendar(self):
        """Initialize Google Calendar."""
        try:
            creds = None
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    cred_files = [f for f in os.listdir('.') if f.startswith('client_secret') and f.endswith('.json')]
                    if cred_files:
                        flow = InstalledAppFlow.from_client_secrets_file(cred_files[0], SCOPES)
                        creds = flow.run_local_server(port=0)
                    else:
                        logger.warning("No Calendar credentials")
                        return
                
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
            
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Calendar service initialized")
        except Exception as e:
            logger.error(f"Calendar init failed: {e}")
            self.service = None
    
    def create_event(self, booking_context: BookingContext) -> Tuple[bool, str]:
        """Create calendar event."""
        if not self.service:
            return False, "Calendar unavailable"
        
        try:
            event_datetime = self._parse_datetime(booking_context.date, booking_context.time)
            if not event_datetime:
                return False, "Invalid date/time"
            
            end_datetime = event_datetime + timedelta(hours=1)
            
            description_parts = [
                f'Service: {booking_context.service}',
                f'Customer: {booking_context.name}'
            ]
            
            if booking_context.notes:
                description_parts.append(f'Notes: {booking_context.notes}')
            
            # Use local timezone instead of hardcoded timezone
            import pytz
            local_tz = pytz.timezone(LOCAL_TIMEZONE)  # Use America/New_York instead of UTC
            
            event = {
                'summary': f'{booking_context.service} - {booking_context.name}',
                'description': '\n'.join(description_parts),
                'start': {'dateTime': event_datetime.isoformat(), 'timeZone': str(local_tz)},
                'end': {'dateTime': end_datetime.isoformat(), 'timeZone': str(local_tz)},
            }
            
            result = self.service.events().insert(calendarId='primary', body=event).execute()
            logger.info(f"Event created: {result.get('id')}")
            return True, result.get('id', '')
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            return False, str(e)
    
    def _parse_datetime(self, date_str: str, time_str: str) -> Optional[datetime]:
        """Parse date and time with proper local timezone handling."""
        try:
            # Handle different time formats
            datetime_str = f"{date_str} {time_str}"
            logger.debug(f"Parsing datetime: '{datetime_str}'")
            logger.debug(f"Input date_str: '{date_str}', time_str: '{time_str}'")
            
            # First try with dateparser which handles natural language better
            # Use local timezone instead of UTC
            parsed_dt = dateparser.parse(datetime_str, settings={
                'PREFER_DATES_FROM': 'future',
                'TIMEZONE': LOCAL_TIMEZONE,
                'TO_TIMEZONE': LOCAL_TIMEZONE,
                'RETURN_AS_TIMEZONE_AWARE': True
            })
            
            if parsed_dt:
                # Ensure the datetime is timezone-aware in local timezone
                if parsed_dt.tzinfo is None:
                    parsed_dt = TIMEZONE_OBJ.localize(parsed_dt)
                logger.info(f"Parsed datetime: {datetime_str} -> {parsed_dt} ({parsed_dt.tzinfo})")
                logger.debug(f"Parsed hour: {parsed_dt.hour}, minute: {parsed_dt.minute}")
                return parsed_dt
                
            # Fallback to dateutil parser
            parsed_dt = dateutil_parser.parse(datetime_str)
            
            # Make sure it's timezone-aware in local timezone
            if parsed_dt.tzinfo is None:
                parsed_dt = TIMEZONE_OBJ.localize(parsed_dt)
            else:
                # Convert to local timezone if it's in a different timezone
                parsed_dt = parsed_dt.astimezone(TIMEZONE_OBJ)
                
            logger.info(f"Fallback parsed datetime: {datetime_str} -> {parsed_dt} ({parsed_dt.tzinfo})")
            logger.debug(f"Fallback parsed hour: {parsed_dt.hour}, minute: {parsed_dt.minute}")
            return parsed_dt
            
        except Exception as e:
            logger.error(f"Datetime parse error for '{date_str} {time_str}': {e}")
            return None

# ===== MAIN AGENT CLASS =====
class VertiqxReceptionistAgent:
    """Enhanced receptionist agent with proper flow control."""
    
    def __init__(self):
        self.context = BookingContext()
        self.database = BookingDatabase()
        self.booking_manager = BookingManager()
        self.calendar = CalendarService()
        self.conversation_history = []
        self.services = SERVICES_CATALOG
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini AI."""
        try:
            # Try both GOOGLE_API_KEY and GEMINI_API_KEY for compatibility
            api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
            if not api_key:
                logger.error("GOOGLE_API_KEY or GEMINI_API_KEY not found")
                return
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini initialized successfully")
        except Exception as e:
            logger.error(f"Gemini init failed: {e}")
            self.model = None
    
    def process_message(self, message: str) -> str:
        """Process user message with proper state management."""
        try:
            message = message.strip()
            
            # Track conversation
            self.conversation_history.append({
                'role': 'user', 
                'text': message, 
                'time': datetime.now()
            })
            
            # Keep last 30 messages
            if len(self.conversation_history) > 30:
                self.conversation_history = self.conversation_history[-30:]
            
            # Generate response based on current state
            response = self._route_message(message)
            
            self.conversation_history.append({
                'role': 'agent', 
                'text': response, 
                'time': datetime.now()
            })
            
            logger.info(f"State: {self.context.state} | User: {message[:50]}... | Agent: {response[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return "Sorry, I didn't quite catch that. Could you say that again?"
    
    def _route_message(self, message: str) -> str:
        """Route message based on conversation state."""
        msg_lower = message.lower().strip()
        
        # Handle based on current state - prioritize active booking flow
        if self.context.state == ConversationState.CONFIRMING_NAME:
            return self._handle_name_confirmation(message)
        
        if self.context.state == ConversationState.CONFIRMING_DATE:
            return self._handle_date_confirmation(message)
        
        if self.context.state == ConversationState.FINAL_CONFIRMATION:
            return self._handle_final_confirmation(message)
            
        if self.context.state == ConversationState.COLLECTING_NAME:
            return self._handle_name_collection(message)
        
        if self.context.state == ConversationState.COLLECTING_DATE:
            return self._handle_date_collection(message)
        
        if self.context.state == ConversationState.COLLECTING_TIME:
            return self._handle_time_collection(message)
        
        # Check for greetings (override state for fresh greeting)
        if self._is_greeting(msg_lower) and len(self.conversation_history) <= 2:
            self.context.state = ConversationState.GREETING
            return "Hi Thanks for reaching out to Vertiqx. How can I help you today?"
        
        # Check for service inquiry
        if self._is_asking_about_services(msg_lower):
            return self._handle_service_list()
        
        # Check for pricing inquiry
        if self._is_asking_about_pricing(msg_lower):
            return self._handle_pricing_inquiry(message)
        
        # Try to extract service from message (only if not in booking flow)
        detected_service = self._detect_service(message)
        if detected_service and not self.context.service_confirmed:
            self.context.service = detected_service
            self.context.service_confirmed = True
            self.context.state = ConversationState.SERVICE_SELECTED
            logger.info(f"Service detected: {detected_service}")
            return self._handle_service_selected()
        
        # Check for booking intent
        if self._has_booking_intent(msg_lower):
            if not self.context.service_confirmed:
                return self._handle_service_list()
            return self._start_booking_flow()
        
        # Default responses
        return self._handle_general_query(msg_lower)
    
    # ===== SERVICE HANDLING =====
    
    def _handle_service_list(self) -> str:
        """Show available services."""
        self.context.state = ConversationState.EXPLORING_SERVICES
        return ("We offer four AI solutions:\n\n"
               " AI Calling Agents\n"
               " WhatsApp Automation\n"
               " Booking Systems\n"
               " Admin Dashboards\n\n"
               "Which interests you?")
    
    def _handle_service_selected(self) -> str:
        """Handle when service is selected."""
        service_info = self.services[self.context.service]
        benefits = "\n".join([f"✓ {b}" for b in service_info['benefits'][:3]])
        
        return (f"**{self.context.service}**\n\n"
               f"{service_info['description']}\n\n"
               f"**Key Benefits:**\n{benefits}\n\n"
               f"Would you like pricing details or a demo?")
    
    def _handle_pricing_inquiry(self, message: str) -> str:
        """Handle pricing requests."""
        # Check if service mentioned in pricing question
        detected_service = self._detect_service(message)
        if detected_service:
            self.context.service = detected_service
            self.context.service_confirmed = True
            return self._show_pricing(detected_service)
        
        # If we already know their service
        if self.context.service_confirmed:
            return self._show_pricing(self.context.service)
        
        # Need to know which service
        return ("I'd be happy to share pricing! Which service interests you?\n\n"
               "• AI Calling Agents\n"
               "• WhatsApp Business Automation\n"
               "• Booking Systems\n"
               "• Admin Dashboards")
    
    def _show_pricing(self, service: str) -> str:
        """Show pricing for a service."""
        if service not in self.services:
            return "Which service would you like pricing for?"
        
        info = self.services[service]
        pricing = info['pricing']
        
        response = f"**{service} Pricing:**\n\n"
        
        for tier, details in pricing.items():
            response += f"💼 **{tier.upper()}** - {details['price']}\n"
            
            capacity = details.get('calls', details.get('messages', details.get('bookings', details.get('users', ''))))
            if capacity:
                response += f"   {capacity}\n"
            
            response += f"   • {details['features'][0]}\n"
            if len(details['features']) > 1:
                response += f"   • {details['features'][1]}\n"
            response += "\n"
        
        return response + "Most businesses start with our Professional tier. Want to schedule a demo to see which fits your needs best?"
    
    # ===== BOOKING FLOW =====
    
    def _start_booking_flow(self) -> str:
        """Start the booking process."""
        if not self.context.service_confirmed:
            return "Which service would you like to schedule a consultation for?"
        
        self.context.state = ConversationState.COLLECTING_NAME
        return f"Perfect! Let's get you scheduled for a {self.context.service} consultation. May I have your name?"
    
    def _handle_name_collection(self, message: str) -> str:
        """Handle name collection."""
        # Extract name from message
        name = self._extract_name_carefully(message)
        
        if not name:
            return "I didn't catch your name. Could you tell me your full name?"
        
        self.context.name = name
        self.context.state = ConversationState.CONFIRMING_NAME
        
        # Spell it out
        spelled = " - ".join([c.upper() for c in name if c.isalpha() or c.isspace()])
        return f"Got it! So that's **{name}**, spelled: {spelled}\n\nIs that correct?"
    
    def _handle_name_confirmation(self, message: str) -> str:
        """Handle name confirmation."""
        msg_lower = message.lower().strip()
        
        # Check for positive confirmation
        if any(word in msg_lower for word in ['yes', 'yeah', 'yep', 'correct', 'right', 'yup', 'exactly', 'perfect', 'good']):
            self.context.name_confirmed = True
            self.context.state = ConversationState.COLLECTING_DATE
            return f"Great! When works for you? I'm available all next week."
        
        # Negative - need correction
        elif any(word in msg_lower for word in ['no', 'nope', 'wrong', 'incorrect', 'not']):
            self.context.name = ""
            self.context.state = ConversationState.COLLECTING_NAME
            return "No problem! What's your name?"
        
        # Check if they're spelling it out (contains individual letters)
        elif self._is_spelling_out(message):
            # They're spelling their name
            corrected_name = self._extract_spelled_name(message)
            if corrected_name:
                self.context.name = corrected_name
                spelled = " - ".join([c.upper() for c in corrected_name if c.isalpha() or c.isspace()])
                return f"Got it! **{corrected_name}**, spelled: {spelled}\n\nCorrect?"
            return "Could you spell it one more time?"
        
        # They might be providing corrected name normally
        else:
            corrected_name = self._extract_name_carefully(message)
            if corrected_name:
                self.context.name = corrected_name
                spelled = " - ".join([c.upper() for c in corrected_name if c.isalpha() or c.isspace()])
                return f"Got it! **{corrected_name}**, spelled: {spelled}\n\nCorrect?"
            return "What's your name?"
    
    def _handle_date_collection(self, message: str) -> str:
        """Handle date collection with improved logic for combined date/time input."""
        # Try to extract both date and time from the message
        date = self._extract_date_carefully(message)
        time = self._extract_time_carefully(message)
        
        if not date:
            return "What day works? (e.g., tomorrow, Monday, Nov 5th)"
        
        # Check if the date is ambiguous (just a day name without "next" or specific date)
        message_lower = message.lower().strip()
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        # If it's just a day name without "next" or "this", ask for clarification
        for day in day_names:
            if day in message_lower and 'next' not in message_lower and 'this' not in message_lower:
                # Check if it's this week or next week
                parsed_date = dateparser.parse(date)
                if parsed_date:
                    today = datetime.now()
                    days_until = (parsed_date.date() - today.date()).days
                    
                    # If it's more than 7 days away, it's likely next week - ask for confirmation
                    if days_until > 7:
                        self.context.date = date  # Store tentatively
                        self.context.state = ConversationState.CONFIRMING_DATE
                        return f"Just to confirm - did you mean {day.title()} of next week ({self._format_date(date)})? Or did you mean this week?"
        
        self.context.date = date
        
        # If time was also provided in the same message, extract it
        if time:
            self.context.time = time
            self.context.state = ConversationState.FINAL_CONFIRMATION
            return self._show_booking_confirmation()
        else:
            self.context.state = ConversationState.COLLECTING_TIME
            return f"Perfect! What time on {self._format_date(date)}?"
    
    def _handle_time_collection(self, message: str) -> str:
        """Handle time collection with improved flow."""
        # First check if time was already provided in the date collection message
        # by looking at the previous user message in conversation history
        if len(self.conversation_history) >= 2:
            prev_user_msg = None
            for i in range(len(self.conversation_history) - 1, -1, -1):
                if self.conversation_history[i]['role'] == 'user':
                    prev_user_msg = self.conversation_history[i]['text']
                    break
            
            if prev_user_msg:
                prev_time = self._extract_time_carefully(prev_user_msg)
                if prev_time and not self.context.time:
                    # Time was already provided in previous message
                    self.context.time = prev_time
                    self.context.state = ConversationState.FINAL_CONFIRMATION
                    return self._show_booking_confirmation()
        
        # Extract time from current message
        time = self._extract_time_carefully(message)
        
        if not time:
            return "What time would you prefer? (e.g., 2pm, 10:30am, 3 o'clock)"
        
        self.context.time = time
        self.context.state = ConversationState.FINAL_CONFIRMATION
        return self._show_booking_confirmation()
    
    def _handle_date_confirmation(self, message: str) -> str:
        """Handle date confirmation when date is ambiguous."""
        msg_lower = message.lower().strip()
        
        # Check if user wants this week or next week
        if any(phrase in msg_lower for phrase in ['this week', 'this', 'earlier', 'sooner']):
            # Recalculate for this week
            day_name = None
            day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in day_names:
                if day in self.context.date.lower():
                    day_name = day
                    break
            
            if day_name:
                # Parse for this week
                parsed = dateparser.parse(f'this {day_name}', settings={
                    'PREFER_DATES_FROM': 'future',
                    'RELATIVE_BASE': datetime.now()
                })
                if parsed:
                    self.context.date = parsed.strftime('%Y-%m-%d')
        
        elif any(phrase in msg_lower for phrase in ['next week', 'next', 'later']):
            # Keep the current date (already set for next week)
            pass
        
        else:
            # If unclear, ask again
            return "Please clarify - do you mean this week or next week?"
        
        # Move to time collection
        self.context.state = ConversationState.COLLECTING_TIME
        return f"Perfect! What time on {self._format_date(self.context.date)}?"
    
    def _show_booking_confirmation(self) -> str:
        """Show final booking confirmation."""
        return (f"Perfect! Let me confirm your consultation:\n\n"
               f"📋 **Service:** {self.context.service}\n"
               f"👤 **Name:** {self.context.name}\n"
               f"📅 **Date:** {self._format_date(self.context.date)}\n"
               f"⏰ **Time:** {self._format_time(self.context.time)}\n\n"
               f"Does everything look good?")
    
    def _handle_final_confirmation(self, message: str) -> str:
        """Handle final booking confirmation."""
        msg_lower = message.lower().strip()
        
        if any(word in msg_lower for word in ['yes', 'yeah', 'yep', 'confirm', 'book', 'perfect', 'correct', 'good', 'looks good']):
            return self._complete_booking()
        elif any(word in msg_lower for word in ['no', 'nope', 'change', 'wrong']):
            self.context.state = ConversationState.COLLECTING_DATE
            return "No problem! What would you like to change?"
        else:
            return "Just confirming - does everything look correct? (yes/no)"
    
    def _complete_booking(self) -> str:
        """Complete the booking."""
        try:
            # Create appointment datetime string for BookingManager
            appointment_datetime_str = f"{self.context.date} {self.context.time}"
            
            # Use BookingManager to create booking with proper timezone handling
            booking_result = self.booking_manager.create_booking(
                name=self.context.name,
                phone="",  # Phone not collected in current flow
                service=self.context.service,
                appointment_time=appointment_datetime_str,
                email="",  # Email not collected in current flow
                notes=self.context.notes
            )
            
            if booking_result['success']:
                self.context.booking_id = booking_result['booking_id']
                logger.info(f"Booking created successfully: {booking_result['booking_id']}")
            else:
                logger.error(f"Booking creation failed: {booking_result.get('error', 'Unknown error')}")
                # Still continue with success message as fallback
                booking_id = f"VTX-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                self.context.booking_id = booking_id
            
            response = (f"🎉 **Excellent! You're all booked, {self.context.name}!**\n\n"
                       f"Your **{self.context.service}** consultation is confirmed:\n"
                       f"📅 {self._format_date(self.context.date)}\n"
                       f"⏰ {self._format_time(self.context.time)}\n\n"
                       f"**Booking ID:** {self.context.booking_id}\n\n"
                       f"We'll send you a reminder before the meeting. "
                       f"Looking forward to showing you what {self.context.service} can do for your business!\n\n"
                       f"Anything else I can help you with?")
            
            # Reset for new conversation
            self.context = BookingContext()
            
            return response
            
        except Exception as e:
            logger.error(f"Booking error: {e}", exc_info=True)
            return f"Perfect! I've got everything noted, {self.context.name}. You'll receive a confirmation shortly!"
    
    # ===== CAREFUL EXTRACTION =====
    
    def _extract_name_carefully(self, text: str) -> Optional[str]:
        """Extract name ONLY when it's clearly a name."""
        text_clean = text.strip()
        text_lower = text_clean.lower()
        
        logger.debug(f"Extracting name from: '{text_clean}'")
        
        # Remove introductory phrases
        prefixes = [
            'my name is ', 'my name\'s ', 'i am ', 'i\'m ', 'this is ',
            'call me ', 'it\'s ', 'its ', 'name is ', 'name\'s ',
            'so my name is ', 'show my name is ', 'my style my name is '
        ]
        
        for prefix in prefixes:
            if text_lower.startswith(prefix):
                text_clean = text_clean[len(prefix):].strip()
                text_lower = text_clean.lower()
                logger.debug(f"Removed prefix '{prefix}', remaining: '{text_clean}'")
                break
        
        # Remove yes/no at start
        for word in ['yes', 'yeah', 'yep', 'no', 'nope', 'so', 'show']:
            if text_lower.startswith(word + ' ') or text_lower.startswith(word + ','):
                text_clean = text_clean[len(word):].strip()
                text_clean = text_clean.lstrip(',').strip()
                text_lower = text_clean.lower()
                logger.debug(f"Removed word '{word}', remaining: '{text_clean}'")
                break
        
        # Check if they're spelling out letters (single letters separated by spaces)
        words_list = text_clean.split()
        single_letters = [w for w in words_list if len(w) == 1 and w.isalpha()]
        
        # If more than 3 single letters, likely spelling - use the spelled name function
        if len(single_letters) > 3:
            logger.debug("Detected spelling out letters")
            return self._extract_spelled_name(text_clean)
        
        # Clean up the remaining text
        if not text_clean:
            logger.debug("No text remaining after cleanup")
            return None
        
        # Remove common non-name words
        non_name_words = ['please', 'thanks', 'thank', 'you', 'hello', 'hi', 'hey']
        words = text_clean.split()
        filtered_words = []
        
        for word in words:
            word_clean = word.strip('.,!?').lower()
            if word_clean not in non_name_words and len(word_clean) > 0:
                # Capitalize first letter for proper name formatting
                filtered_words.append(word.strip('.,!?').capitalize())
        
        if not filtered_words:
            logger.debug("No valid name words found")
            return None
        
        # Join the words to form the name
        extracted_name = ' '.join(filtered_words)
        
        # Basic validation - name should be 1-4 words, each 2+ characters
        name_words = extracted_name.split()
        if len(name_words) > 4:
            logger.debug(f"Too many words for a name: {len(name_words)}")
            return None
        
        # Check if all words look like names (alphabetic, reasonable length)
        for word in name_words:
            if not word.isalpha() or len(word) < 2:
                logger.debug(f"Invalid name word: '{word}'")
                return None
        
        logger.debug(f"Extracted name: '{extracted_name}'")
        return extracted_name
    
    def _extract_date_carefully(self, text: str) -> Optional[str]:
        """Extract date ONLY when clearly present."""
        try:
            text_lower = text.lower().strip()
            
            # Must contain date indicators
            date_indicators = [
                'tomorrow', 'today', 'monday', 'tuesday', 'wednesday', 'thursday',
                'friday', 'saturday', 'sunday', 'next', 'this',
                'january', 'february', 'march', 'april', 'may', 'june',
                'july', 'august', 'september', 'october', 'november', 'december',
                'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
            ]
            
            # Check if any date indicator is present
            has_date_indicator = any(indicator in text_lower for indicator in date_indicators)
            has_date_format = bool(re.search(r'\d{1,2}[/-]\d{1,2}', text)) or bool(re.search(r'\d{1,2}(?:st|nd|rd|th)', text_lower))
            
            if not (has_date_indicator or has_date_format):
                return None
            
            # Special handling for day names
            day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in day_names:
                if day in text_lower:
                    # Check if it's "next [day]" or just "[day]"
                    if f'next {day}' in text_lower:
                        # Explicitly next week
                        parsed = dateparser.parse(f'next {day}', settings={
                            'PREFER_DATES_FROM': 'future',
                            'RELATIVE_BASE': datetime.now()
                        })
                    else:
                        # Just the day name - find next occurrence
                        parsed = dateparser.parse(day, settings={
                            'PREFER_DATES_FROM': 'future',
                            'RELATIVE_BASE': datetime.now()
                        })
                    
                    if parsed and parsed.date() >= datetime.now().date():
                        return parsed.strftime('%Y-%m-%d')
            
            # Parse other date formats
            parsed = dateparser.parse(text, settings={
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': datetime.now()
            })
            
            if parsed and parsed.date() >= datetime.now().date():
                return parsed.strftime('%Y-%m-%d')
                
        except Exception as e:
            logger.debug(f"Date parsing failed: {e}")
        
        return None
    
    def _extract_time_carefully(self, text: str) -> Optional[str]:
        """Extract time ONLY when clearly present."""
        try:
            text_lower = text.lower().strip()
            logger.debug(f"Extracting time from: '{text}' -> '{text_lower}'")
            
            # Must contain time indicators
            time_indicators = ['am', 'pm', 'morning', 'afternoon', 'evening', 'noon', 'o\'clock', 'oclock', ':']
            
            has_indicator = any(indicator in text_lower for indicator in time_indicators)
            logger.debug(f"Has time indicator: {has_indicator}")
            
            if not has_indicator:
                return None
            
            # Clean up common prefixes that might interfere with parsing
            prefixes_to_remove = ['around', 'about', 'approximately', 'roughly', 'near', 'close to', 'at']
            cleaned_text = text_lower
            for prefix in prefixes_to_remove:
                if cleaned_text.startswith(prefix + ' '):
                    cleaned_text = cleaned_text[len(prefix):].strip()
            
            logger.debug(f"Cleaned text: '{cleaned_text}'")
            
            # Handle special cases first
            if 'noon' in cleaned_text:
                return '12:00 PM'
            elif 'midnight' in cleaned_text:
                return '12:00 AM'
            
            # Try to parse time with enhanced patterns - more specific first
            patterns = [
                r'(\d{1,2}):(\d{2})\s*(p\.?m\.?|pm)',  # 6:00pm, 6:00 p.m.
                r'(\d{1,2}):(\d{2})\s*(a\.?m\.?|am)',  # 6:00am, 6:00 a.m.
                r'(\d{1,2})\s*(p\.?m\.?|pm)',          # 6pm, 6 p.m.
                r'(\d{1,2})\s*(a\.?m\.?|am)',          # 6am, 6 a.m.
                r'(\d{1,2})\s*o\'?clock',              # 6 oclock, 6 o'clock
                r'(\d{1,2}):(\d{2})',                  # 14:30 (24-hour format)
            ]
            
            for i, pattern in enumerate(patterns):
                match = re.search(pattern, cleaned_text)
                if match:
                    time_str = match.group(0).strip()
                    logger.debug(f"Pattern {i} matched: '{time_str}'")
                    
                    # Clean up spacing and dots in AM/PM
                    time_str = re.sub(r'\s*([ap])\.?\s*m\.?', r' \1m', time_str)
                    time_str = re.sub(r'\s+', ' ', time_str)  # normalize spaces
                    
                    logger.debug(f"Trying to parse time: '{time_str}'")
                    
                    # Use dateparser with specific settings
                    parsed = dateparser.parse(time_str, settings={
                        'PREFER_DATES_FROM': 'future',
                        'STRICT_PARSING': True
                    })
                    
                    if parsed:
                        # Return in 12-hour format to maintain consistency
                        result_time = parsed.strftime('%I:%M %p').lstrip('0')
                        logger.debug(f"Successfully parsed '{time_str}' -> '{result_time}'")
                        return result_time
            
            # Try general parsing with the cleaned text as fallback
            parsed = dateparser.parse(cleaned_text, settings={
                'PREFER_DATES_FROM': 'future',
                'STRICT_PARSING': False
            })
            
            if parsed and parsed.time() != parsed.time().replace(hour=0, minute=0, second=0):
                # Return in 12-hour format to maintain consistency
                result_time = parsed.strftime('%I:%M %p').lstrip('0')
                logger.debug(f"Fallback parsed '{cleaned_text}' -> '{result_time}'")
                return result_time
                
        except Exception as e:
            logger.debug(f"Time parsing failed: {e}")
        
        return None
    
    def _detect_service(self, text: str) -> Optional[str]:
        """Detect service with high precision."""
        text_lower = text.lower().strip()
        
        # AI Calling Agents
        calling_patterns = [
            'ai calling', 'calling agent', 'call agent', 'voice ai',
            'phone ai', 'ai call', 'calling agents', 'ai voice'
        ]
        if any(pattern in text_lower for pattern in calling_patterns):
            return "AI Calling Agents"
        
        # WhatsApp
        whatsapp_patterns = [
            'whatsapp', 'whats app', 'wa business', 'wa automation',
            'whatsapp automation', 'whatsapp business'
        ]
        if any(pattern in text_lower for pattern in whatsapp_patterns):
            return "WhatsApp Business Automation"
        
        # Booking Systems
        booking_patterns = [
            'booking system', 'appointment system', 'scheduling system',
            'reservation system', 'booking', 'appointment'
        ]
        # Must have "system" or be specific
        if any(pattern in text_lower for pattern in booking_patterns):
            return "Booking Systems"
        
        # Admin Dashboards
        dashboard_patterns = [
            'admin dashboard', 'dashboard', 'analytics dashboard',
            'business dashboard', 'admin', 'analytics'
        ]
        if any(pattern in text_lower for pattern in dashboard_patterns):
            return "Admin Dashboards"
        
        return None
    
    def _is_spelling_out(self, text: str) -> bool:
        """Check if user is spelling out a name letter by letter."""
        text_lower = text.lower().strip()
        
        # Look for patterns like "a d e e m" or "spelling is a d e"
        if any(keyword in text_lower for keyword in ['spelling', 'spell', 'spelled']):
            return True
        
        # Check if text has many single letters separated by spaces
        words = text_lower.split()
        single_letters = [w for w in words if len(w) == 1 and w.isalpha()]
        
        # If more than 3 single letters, likely spelling
        return len(single_letters) > 3
    
    def _extract_spelled_name(self, text: str) -> Optional[str]:
        """Extract name from spelled-out letters."""
        text_lower = text.lower().strip()
        
        # Remove common phrases
        text_lower = re.sub(r'(my name is|name is|spelling is|spelled|spell|it\'?s|so|show|style|my)\s*', '', text_lower)
        
        # Get all words
        words = text_lower.split()
        
        # Separate single letters from regular words
        single_letters = []
        regular_words = []
        
        for w in words:
            if len(w) == 1 and w.isalpha():
                single_letters.append(w.upper())
            elif len(w) > 1 and w.isalpha():
                regular_words.append(w.capitalize())
        
        # If we have single letters (more than 2), use those
        if len(single_letters) > 2:
            spelled_part = ''.join(single_letters).capitalize()
            # Combine with any regular words
            if regular_words:
                return f"{' '.join(regular_words)} {spelled_part}".strip()
            return spelled_part
        
        # Otherwise use regular words
        if regular_words:
            return ' '.join(regular_words)
        
        return None
    
    # ===== INTENT DETECTION =====
    
    def _is_greeting(self, text: str) -> bool:
        """Check if message is a greeting."""
        greetings = ['hello', 'hi ', 'hey', 'good morning', 'good afternoon', 
                    'good evening', 'greetings', 'howdy']
        # Check if starts with or is exactly a greeting
        return any(text.startswith(g) or text == g.strip() for g in greetings)
    
    def _is_asking_about_services(self, text: str) -> bool:
        """Check if asking about services."""
        patterns = [
            'what service', 'what do you offer', 'tell me about your service',
            'your service', 'what you offer', 'what can you do',
            'what does vertiqx', 'services you offer', 'available service',
            'do you offer', 'tell me about service'
        ]
        return any(pattern in text for pattern in patterns)
    
    def _is_asking_about_pricing(self, text: str) -> bool:
        """Check if asking about pricing."""
        pricing_words = ['price', 'pricing', 'cost', 'how much', 'expensive', 
                        'rate', 'fee', 'charge', 'afford', 'budget']
        return any(word in text for word in pricing_words)
    
    def _has_booking_intent(self, text: str) -> bool:
        """Check if user wants to book."""
        # Must be explicit about booking/scheduling
        booking_phrases = [
            'book', 'schedule', 'appointment', 'consultation', 'meeting',
            'schedule a', 'book a', 'set up', 'arrange', 'demo',
            'get started', 'sign up', 'i want to book', 'want to schedule'
        ]
        return any(phrase in text for phrase in booking_phrases)
    
    def _handle_general_query(self, text: str) -> str:
        """Handle general queries."""
        # Thank you
        if 'thank' in text:
            return "You're very welcome! Is there anything else I can help you with?"
        
        # Goodbye
        if any(word in text for word in ['bye', 'goodbye', 'see you', 'later', 'have a good']):
            return "Thanks for chatting with Vertiqx! Feel free to reach out anytime. Have a great day! 👋"
        
        # About agent
        if any(phrase in text for phrase in ['who are you', 'what are you', 'about you', 'are you ai', 'are you bot']):
            return ("I'm your Vertiqx AI assistant! I help businesses discover the perfect AI solutions "
                   "for their needs. Think of me as your friendly guide to automation. "
                   "I can tell you about our services, discuss pricing, or help you schedule a consultation. "
                   "What interests you?")
        
        # Default
        if self.context.service_confirmed:
            return (f"I can tell you more about {self.context.service}, share pricing details, "
                   f"or get you scheduled for a consultation. What would you like to do?")
        else:
            return ("I'm here to help! I can:\n"
                   "• Tell you about our AI solutions\n"
                   "• Share pricing information\n"
                   "• Schedule a consultation\n\n"
                   "What would you like to explore?")
    
    # ===== FORMATTING HELPERS =====
    
    def _format_date(self, date_str: str) -> str:
        """Format date nicely."""
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%A, %B %d, %Y')
        except:
            return date_str
    
    def _format_time(self, time_str: str) -> str:
        """Format time nicely."""
        try:
            # If it's already in 12-hour format (contains AM/PM), return as is
            if 'AM' in time_str.upper() or 'PM' in time_str.upper():
                return time_str
            
            # Otherwise, assume it's 24-hour format and convert
            hour, minute = map(int, time_str.split(':'))
            if hour == 0:
                return f"12:{minute:02d} AM"
            elif hour < 12:
                return f"{hour}:{minute:02d} AM"
            elif hour == 12:
                return f"12:{minute:02d} PM"
            else:
                return f"{hour-12}:{minute:02d} PM"
        except:
            return time_str
    
    def reset(self):
        """Reset conversation."""
        self.context = BookingContext()
        self.conversation_history = []
        logger.info("Conversation reset")
    
    def get_current_status(self) -> Dict:
        """Get current booking status."""
        return {
            'state': self.context.state,
            'name': self.context.name,
            'name_confirmed': self.context.name_confirmed,
            'service': self.context.service,
            'service_confirmed': self.context.service_confirmed,
            'date': self.context.date,
            'time': self.context.time,
            'booking_id': self.context.booking_id
        }

# ===== MAIN =====
def main():
    """Main function for testing."""
    print("\n" + "="*70)
    print("🤖 Vertiqx Receptionist Agent - Fixed & Enhanced")
    print("="*70)
    print("\nCommands:")
    print("  'quit' or 'exit' - End conversation")
    print("  'reset' - Start fresh conversation")
    print("  'status' - View current booking details")
    print("="*70 + "\n")
    
    agent = VertiqxReceptionistAgent()
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit']:
                print("\n🤖 Agent: Thanks for chatting with Vertiqx! Have an amazing day! 👋")
                break
            
            elif user_input.lower() == 'reset':
                agent.reset()
                print("\n🤖 Agent: Fresh start! How can I help you today?")
                continue
            
            elif user_input.lower() == 'status':
                status = agent.get_current_status()
                print("\n" + "="*50)
                print("📊 CURRENT BOOKING STATUS")
                print("="*50)
                for key, value in status.items():
                    if value:
                        print(f"  {key}: {value}")
                print("="*50)
                continue
            
            # Process message
            response = agent.process_message(user_input)
            print(f"\n🤖 Agent: {response}")
            
        except KeyboardInterrupt:
            print("\n\n🤖 Agent: Thanks for your time! Take care! 👋")
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}", exc_info=True)
            print("\n🤖 Agent: Oops, something went wrong. Let's try that again!")

if __name__ == "__main__":
    main()