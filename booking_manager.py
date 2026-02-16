#!/usr/bin/env python3
"""
Booking Manager for Vertiqx AI Agent
Handles customer information collection, booking creation, and management.
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import re
from google_calendar_integration import GoogleCalendarIntegration

logger = logging.getLogger(__name__)

@dataclass
class Customer:
    """Customer information data class."""
    name: str = ""
    phone: str = ""
    email: str = ""
    created_at: str = ""
    
    def is_complete(self) -> bool:
        """Check if all required customer information is provided."""
        return bool(self.name and self.phone and self.email)
    
    def missing_fields(self) -> List[str]:
        """Return list of missing required fields."""
        missing = []
        if not self.name:
            missing.append("full name")
        if not self.phone:
            missing.append("phone number")
        if not self.email:
            missing.append("email")
        return missing

@dataclass
class Booking:
    """Booking information data class."""
    booking_id: str = ""
    customer_name: str = ""
    customer_phone: str = ""
    customer_email: str = ""
    service_type: str = ""
    booking_date: str = ""
    booking_time: str = ""
    status: str = "pending"  # pending, confirmed, cancelled, completed
    notes: str = ""
    created_at: str = ""
    
    def to_dict(self) -> Dict:
        """Convert booking to dictionary."""
        return asdict(self)

class BookingManager:
    """Manages customer information and bookings."""
    
    def __init__(self, db_path: str = "vertiqx_bookings.db"):
        self.db_path = db_path
        self.init_database()
        
        # Initialize Google Calendar integration
        try:
            self.google_calendar = GoogleCalendarIntegration()
            logger.info("Google Calendar integration initialized successfully")
        except Exception as e:
            logger.warning(f"Google Calendar integration failed: {e}")
            self.google_calendar = None
        
        # Service types offered
        self.service_types = [
            "WhatsApp Automation",
            "AI Calling Agent", 
            "Booking System",
            "Dashboard Solutions"
        ]
    
    def init_database(self):
        """Initialize the SQLite database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create customers table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS customers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        created_at TEXT NOT NULL
                    )
                """)
                
                # Create bookings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bookings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        booking_id TEXT UNIQUE NOT NULL,
                        customer_name TEXT NOT NULL,
                        customer_phone TEXT NOT NULL,
                        customer_email TEXT NOT NULL,
                        service_type TEXT NOT NULL,
                        booking_date TEXT,
                        booking_time TEXT,
                        status TEXT DEFAULT 'pending',
                        notes TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        # Check if it's a valid length (10-15 digits)
        return 10 <= len(digits_only) <= 15
    
    def format_phone(self, phone: str) -> str:
        """Format phone number consistently."""
        digits_only = re.sub(r'\D', '', phone)
        if len(digits_only) == 10:
            return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
        elif len(digits_only) == 11 and digits_only[0] == '1':
            return f"+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
        else:
            return phone  # Return original if can't format
    
    def extract_customer_info(self, text: str) -> Customer:
        """Extract customer information from text using advanced patterns."""
        customer = Customer()
        text_lower = text.lower()
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match and self.validate_email(email_match.group()):
            customer.email = email_match.group().lower()
        
        # Extract phone number
        phone_patterns = [
            r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            r'(\+?1[-.\s]?)?([0-9]{3})[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            r'(\+?1[-.\s]?)?([0-9]{10})'
        ]
        
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                phone = phone_match.group()
                if self.validate_phone(phone):
                    customer.phone = self.format_phone(phone)
                    break
        
        # Extract name using various patterns
        name_patterns = [
            r'my name is\s+([A-Za-z\s]+?)(?:\s|$|[.,!?])',
            r'i\'?m\s+([A-Za-z\s]+?)(?:\s|$|[.,!?])',
            r'this is\s+([A-Za-z\s]+?)(?:\s|$|[.,!?])',
            r'name:\s*([A-Za-z\s]+?)(?:\s|$|[.,!?])',
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, text_lower)
            if name_match:
                name = name_match.group(1).strip().title()
                # Validate name (at least 2 characters, only letters and spaces)
                if len(name) >= 2 and re.match(r'^[A-Za-z\s]+$', name):
                    customer.name = name
                    break
        
        customer.created_at = datetime.now().isoformat()
        return customer
    
    def save_customer(self, customer: Customer) -> bool:
        """Save customer to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO customers 
                    (name, phone, email, created_at) 
                    VALUES (?, ?, ?, ?)
                """, (customer.name, customer.phone, customer.email, customer.created_at))
                conn.commit()
                logger.info(f"Customer saved: {customer.name} ({customer.email})")
                return True
        except Exception as e:
            logger.error(f"Error saving customer: {e}")
            return False
    
    def find_customer(self, email: str = None, phone: str = None, name: str = None) -> Optional[Customer]:
        """Find customer by email, phone, or name."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if email:
                    cursor.execute("SELECT * FROM customers WHERE email = ?", (email.lower(),))
                elif phone:
                    cursor.execute("SELECT * FROM customers WHERE phone = ?", (phone,))
                elif name:
                    cursor.execute("SELECT * FROM customers WHERE name LIKE ?", (f"%{name}%",))
                else:
                    return None
                
                row = cursor.fetchone()
                if row:
                    return Customer(
                        name=row[1],
                        phone=row[2],
                        email=row[3],
                        created_at=row[4]
                    )
                return None
        except Exception as e:
            logger.error(f"Error finding customer: {e}")
            return None
    
    def create_booking(self, customer: Customer, service_type: str, notes: str = "") -> Optional[Booking]:
        """Create a new booking."""
        if not customer.is_complete():
            logger.warning(f"Incomplete customer info for booking: {customer.missing_fields()}")
            return None
        
        try:
            # Generate booking ID
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            booking_id = f"VTX-{timestamp}"
            
            booking = Booking(
                booking_id=booking_id,
                customer_name=customer.name,
                customer_phone=customer.phone,
                customer_email=customer.email,
                service_type=service_type,
                status="pending",
                notes=notes,
                created_at=datetime.now().isoformat()
            )
            
            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO bookings 
                    (booking_id, customer_name, customer_phone, customer_email, 
                     service_type, booking_date, booking_time, status, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    booking.booking_id, booking.customer_name, booking.customer_phone,
                    booking.customer_email, booking.service_type, booking.booking_date,
                    booking.booking_time, booking.status, booking.notes, booking.created_at
                ))
                conn.commit()
            
            # Save customer info
            self.save_customer(customer)
            
            logger.info(f"Booking created: {booking_id} for {customer.name}")
            return booking
            
        except Exception as e:
            logger.error(f"Error creating booking: {e}")
            return None
    
    def create_booking(self, name: str, phone: str, service: str, appointment_time: str, 
                      email: str = "", notes: str = "") -> Dict:
        """Create a new booking with individual parameters and Google Calendar integration."""
        try:
            # Parse appointment time to extract date and time
            appointment_datetime = self._parse_appointment_time(appointment_time)
            if not appointment_datetime:
                return {
                    'success': False,
                    'error': 'Invalid appointment time format'
                }
            
            appointment_date = appointment_datetime.strftime("%Y-%m-%d")
            appointment_time_str = appointment_datetime.strftime("%H:%M")
            
            # Generate booking ID
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            booking_id = f"VTX-{timestamp}"
            
            # Create Google Calendar event if integration is available
            google_event_id = None
            if self.google_calendar:
                try:
                    # Create calendar event
                    event_result = self.google_calendar.create_appointment(
                        title=f"{service} - {name}",
                        description=f"Service: {service}\nCustomer: {name}\nPhone: {phone}\nNotes: {notes}",
                        start_time=appointment_datetime,
                        duration_minutes=60,  # Default 1 hour
                        attendee_email=email if email else None
                    )
                    
                    if event_result['success']:
                        google_event_id = event_result['event_id']
                        logger.info(f"Google Calendar event created: {google_event_id}")
                    else:
                        logger.warning(f"Failed to create Google Calendar event: {event_result['error']}")
                        
                except Exception as e:
                    logger.warning(f"Google Calendar integration error: {e}")
            
            # Save to database using the updated booking_database
            from booking_database import BookingDatabase
            db = BookingDatabase()
            
            booking_result = db.add_booking(
                customer_name=name,
                service_name=service,
                appointment_time=appointment_time_str,
                appointment_date=appointment_date,
                customer_phone=phone,
                customer_email=email,
                google_calendar_event_id=google_event_id,
                notes=notes
            )
            
            if booking_result:
                logger.info(f"Booking created successfully: {booking_id}")
                return {
                    'success': True,
                    'booking_id': booking_id,
                    'google_event_id': google_event_id,
                    'message': f"Booking confirmed! ID: {booking_id}"
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to save booking to database'
                }
                
        except Exception as e:
            logger.error(f"Error creating booking: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_appointment_time(self, appointment_time: str) -> Optional[datetime]:
        """Parse appointment time string to datetime object."""
        try:
            # Try different time formats
            time_formats = [
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d %I:%M %p",
                "%m/%d/%Y %H:%M",
                "%m/%d/%Y %I:%M %p",
                "%d/%m/%Y %H:%M",
                "%d/%m/%Y %I:%M %p"
            ]
            
            for fmt in time_formats:
                try:
                    return datetime.strptime(appointment_time, fmt)
                except ValueError:
                    continue
            
            # If no format matches, try to parse relative times like "tomorrow at 2pm"
            # For now, return None - this can be enhanced later
            logger.warning(f"Could not parse appointment time: {appointment_time}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing appointment time: {e}")
            return None
    
    def find_booking(self, booking_id: str = None, customer_email: str = None, 
                    customer_name: str = None) -> Optional[Booking]:
        """Find booking by ID, customer email, or name."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if booking_id:
                    cursor.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
                elif customer_email:
                    cursor.execute("""
                        SELECT * FROM bookings WHERE customer_email = ? 
                        ORDER BY created_at DESC LIMIT 1
                    """, (customer_email.lower(),))
                elif customer_name:
                    cursor.execute("""
                        SELECT * FROM bookings WHERE customer_name LIKE ? 
                        ORDER BY created_at DESC LIMIT 1
                    """, (f"%{customer_name}%",))
                else:
                    return None
                
                row = cursor.fetchone()
                if row:
                    return Booking(
                        booking_id=row[1],
                        customer_name=row[2],
                        customer_phone=row[3],
                        customer_email=row[4],
                        service_type=row[5],
                        booking_date=row[6] or "",
                        booking_time=row[7] or "",
                        status=row[8],
                        notes=row[9] or "",
                        created_at=row[10]
                    )
                return None
        except Exception as e:
            logger.error(f"Error finding booking: {e}")
            return None
    
    def cancel_booking(self, booking_id: str = None, customer_email: str = None, 
                      customer_name: str = None) -> bool:
        """Cancel a booking."""
        booking = self.find_booking(booking_id, customer_email, customer_name)
        if not booking:
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE bookings SET status = 'cancelled' 
                    WHERE booking_id = ?
                """, (booking.booking_id,))
                conn.commit()
            
            logger.info(f"Booking cancelled: {booking.booking_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling booking: {e}")
            return False
    
    def get_booking_summary(self, booking: Booking) -> str:
        """Generate a booking summary for confirmation."""
        summary = f"""
📋 Booking Confirmation
Booking ID: {booking.booking_id}
Customer: {booking.customer_name}
Phone: {booking.customer_phone}
Email: {booking.customer_email}
Service: {booking.service_type}
Date: {booking.booking_date}
Time: {booking.booking_time}
Status: {booking.status}
Notes: {booking.notes}
"""
        return summary.strip()
    
    def get_all_bookings(self, status: str = None) -> List[Booking]:
        """Get all bookings, optionally filtered by status."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if status:
                    cursor.execute("SELECT * FROM bookings WHERE status = ? ORDER BY created_at DESC", (status,))
                else:
                    cursor.execute("SELECT * FROM bookings ORDER BY created_at DESC")
                
                bookings = []
                for row in cursor.fetchall():
                    booking = Booking(
                        booking_id=row[1],
                        customer_name=row[2],
                        customer_phone=row[3],
                        customer_email=row[4],
                        service_type=row[5],
                        booking_date=row[6] or "",
                        booking_time=row[7] or "",
                        status=row[8],
                        notes=row[9] or "",
                        created_at=row[10]
                    )
                    bookings.append(booking)
                
                return bookings
        except Exception as e:
            logger.error(f"Error getting bookings: {e}")
            return []
    
    def update_booking_status(self, booking_id: str, new_status: str) -> bool:
        """Update booking status."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE bookings SET status = ? WHERE booking_id = ?
                """, (new_status, booking_id))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Booking {booking_id} status updated to {new_status}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating booking status: {e}")
            return False
    
    def get_service_types(self) -> List[str]:
        """Get available service types."""
        return [
            "automated booking services",
            "whatsapp automation",
            "ai customer support",
            "car detailing",
            "appointment scheduling",
            "consultation",
            "general inquiry"
        ]
    
    def detect_service_type(self, text: str) -> str:
        """Detect service type from customer message."""
        text_lower = text.lower()
        
        service_keywords = {
            "car detailing": ["car", "detailing", "wash", "clean", "vehicle", "auto"],
            "whatsapp automation": ["whatsapp", "messaging", "chat", "automation"],
            "ai customer support": ["support", "help", "assistance", "ai", "customer service"],
            "automated booking services": ["booking", "appointment", "schedule", "reserve"],
            "consultation": ["consultation", "consult", "advice", "meeting"],
            "appointment scheduling": ["appointment", "schedule", "meeting", "time"]
        }
        
        for service, keywords in service_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return service
        
        return "general inquiry"
    
    def generate_booking_report(self) -> str:
        """Generate a summary report of all bookings."""
        try:
            bookings = self.get_all_bookings()
            
            if not bookings:
                return "No bookings found."
            
            status_counts = {}
            service_counts = {}
            
            for booking in bookings:
                # Count by status
                status_counts[booking.status] = status_counts.get(booking.status, 0) + 1
                # Count by service
                service_counts[booking.service_type] = service_counts.get(booking.service_type, 0) + 1
            
            report = f"""
📊 Booking Report
Total Bookings: {len(bookings)}

Status Breakdown:
"""
            for status, count in status_counts.items():
                report += f"  {status.title()}: {count}\n"
            
            report += "\nService Breakdown:\n"
            for service, count in service_counts.items():
                report += f"  {service.title()}: {count}\n"
            
            return report.strip()
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return "Error generating booking report."


def test_booking_manager():
    """Test the booking manager functionality."""
    print("Testing Booking Manager...")
    
    # Initialize manager
    manager = BookingManager()
    
    # Test customer creation
    customer_text = "Hi, I'm John Doe, my phone is 555-123-4567 and email is john@example.com"
    customer_info = manager.extract_customer_info(customer_text)
    print(f"Extracted customer info: {customer_info}")
    
    # Test booking creation
    if customer_info:
        booking = manager.create_booking(
            customer_info,
            service_type="car detailing",
            booking_date="2024-01-15",
            booking_time="10:00 AM",
            notes="First time customer"
        )
        if booking:
            print(f"Created booking: {booking.booking_id}")
            print(manager.get_booking_summary(booking))
    
    # Test service detection
    test_messages = [
        "I need car detailing service",
        "Help with WhatsApp automation",
        "Schedule an appointment",
        "I need customer support"
    ]
    
    for msg in test_messages:
        service = manager.detect_service_type(msg)
        print(f"'{msg}' -> {service}")
    
    # Generate report
    print("\n" + manager.generate_booking_report())


if __name__ == "__main__":
    test_booking_manager()