"""
Booking Database Module for Vertiqx Voice Agent
===============================================
Handles all database operations for appointment bookings with extensive commenting
for easy modification and maintenance.

MAIN FEATURES:
- SQLite database for local storage (easily changeable to other databases)
- Booking creation, retrieval, updating, and deletion
- Availability checking to prevent double bookings
- Integration with Google Calendar event IDs
- Comprehensive logging for debugging and monitoring

MODIFICATION GUIDE:
- Search for "MODIFY HERE" comments to find customization points
- Database schema can be easily extended by modifying the create_tables method
- Connection string can be changed to use PostgreSQL, MySQL, etc.
"""

import sqlite3
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json

# ===== LOGGING SETUP =====
# MODIFY HERE: Change logging configuration if needed
logger = logging.getLogger(__name__)

# ===== BOOKING DATA CLASS =====
@dataclass
class Booking:
    """
    Represents a single booking record.
    
    MODIFY HERE: Add new fields if you need to store additional booking information
    """
    id: Optional[int] = None              # Database ID (auto-generated)
    customer_name: str = ""               # Customer's full name
    customer_phone: str = ""              # Customer's phone number
    customer_email: str = ""              # Customer's email address
    service_name: str = ""                # Name of the booked service
    appointment_date: str = ""            # Date of appointment (YYYY-MM-DD format)
    appointment_time: str = ""            # Time of appointment (HH:MM format)
    status: str = "confirmed"     # Status: confirmed, cancelled, completed
    notes: str = ""                       # Additional notes about the booking
    google_calendar_event_id: str = ""    # Google Calendar event ID for integration
    created_at: Optional[datetime] = None # When the booking was created
    updated_at: Optional[datetime] = None # When the booking was last updated
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert booking to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_email': self.customer_email,
            'service_name': self.service_name,
            'appointment_date': self.appointment_date,
            'appointment_time': self.appointment_time,
            'status': self.status,
            'notes': self.notes,
            'google_calendar_event_id': self.google_calendar_event_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# ===== MAIN DATABASE CLASS =====
class BookingDatabase:
    """
    Main database class for handling all booking operations.
    
    MODIFY HERE: Change database type, connection parameters, or add new methods
    """
    
    def __init__(self, db_path: str = "vertiqx_bookings.db"):
        """
        Initialize the booking database.
        
        MODIFY HERE: Change database path or connection parameters
        """
        self.db_path = db_path
        self.connection = None
        
        # Initialize database and create tables
        self._initialize_database()
        logger.info(f"BookingDatabase initialized with database: {db_path}")
    
    def _initialize_database(self):
        """
        Initialize database connection and create tables if they don't exist.
        
        MODIFY HERE: Change database initialization logic
        """
        try:
            # Create database directory if it doesn't exist
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
            
            # Connect to database
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            
            # Create tables
            self._create_tables()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _create_tables(self):
        """
        Create database tables if they don't exist.
        
        MODIFY HERE: Add new tables or modify existing table schema
        """
        try:
            cursor = self.connection.cursor()
            
            # Main bookings table
            # MODIFY HERE: Add new columns or change data types
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT NOT NULL,
                    customer_phone TEXT NOT NULL,
                    customer_email TEXT,
                    service_name TEXT NOT NULL,
                    appointment_date TEXT NOT NULL,
                    appointment_time TEXT NOT NULL,
                    status TEXT DEFAULT 'confirmed',
                    notes TEXT,
                    google_calendar_event_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index for faster queries
            # MODIFY HERE: Add more indexes for performance optimization
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_appointment_datetime 
                ON bookings(appointment_date, appointment_time)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_customer_phone 
                ON bookings(customer_phone)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_booking_status 
                ON bookings(status)
            """)
            
            # Services table (optional - for managing available services)
            # MODIFY HERE: Customize available services
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT UNIQUE NOT NULL,
                    service_description TEXT,
                    duration_minutes INTEGER DEFAULT 60,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default services if table is empty
            cursor.execute("SELECT COUNT(*) FROM services")
            if cursor.fetchone()[0] == 0:
                default_services = [
                    ('AI Calling Agent', 'Automated phone systems for customer service', 60),
                    ('WhatsApp Business Automation', 'Automated messaging and customer support', 45),
                    ('Booking System', 'Online appointment scheduling solutions', 90),
                    ('Admin Dashboard', 'Business management and analytics platforms', 120)
                ]
                
                cursor.executemany("""
                    INSERT INTO services (service_name, service_description, duration_minutes)
                    VALUES (?, ?, ?)
                """, default_services)
            
            self.connection.commit()
            logger.info("Database tables created/verified successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def add_booking(self, customer_name: str, service_name: str, appointment_time: str, 
                   appointment_date: str, customer_phone: str, customer_email: str = "",
                   notes: str = "", google_calendar_event_id: str = "") -> Optional[int]:
        """
        Add a new booking to the database.
        
        MODIFY HERE: Add validation rules or additional fields
        
        Args:
            customer_name: Customer's full name
            service_name: Name of the service being booked
            appointment_time: Time of appointment (e.g., "2:00 PM")
            appointment_date: Date of appointment (e.g., "2024-01-15")
            customer_phone: Customer's phone number
            customer_email: Customer's email address (optional)
            notes: Additional notes about the booking
            google_calendar_event_id: Google Calendar event ID for integration
            
        Returns:
            Booking ID if successful, None if failed
        """
        try:
            # Validate required fields
            if not all([customer_name, service_name, appointment_time, appointment_date, customer_phone]):
                logger.error("Missing required fields for booking")
                return None
            
            # Check if time slot is already booked
            if self.is_time_slot_booked(appointment_date, appointment_time):
                logger.warning(f"Time slot already booked: {appointment_date} at {appointment_time}")
                return None
            
            # Normalize date format
            normalized_date = self._normalize_date(appointment_date)
            if not normalized_date:
                logger.error(f"Invalid date format: {appointment_date}")
                return None
            
            # Normalize time format
            normalized_time = self._normalize_time(appointment_time)
            if not normalized_time:
                logger.error(f"Invalid time format: {appointment_time}")
                return None
            
            cursor = self.connection.cursor()
            
            # Insert booking
            cursor.execute("""
                INSERT INTO bookings (
                    customer_name, customer_phone, customer_email, service_name,
                    appointment_date, appointment_time, notes, google_calendar_event_id,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_name.strip() if customer_name else "",
                customer_phone.strip() if customer_phone else "",
                customer_email.strip() if customer_email else "",
                service_name.strip() if service_name else "",
                normalized_date,
                normalized_time,
                notes.strip() if notes else "",
                google_calendar_event_id.strip() if google_calendar_event_id else "",
                datetime.now(),
                datetime.now()
            ))
            
            booking_id = cursor.lastrowid
            self.connection.commit()
            
            logger.info(f"Booking added successfully: ID {booking_id}")
            return booking_id
            
        except Exception as e:
            logger.error(f"Failed to add booking: {e}")
            self.connection.rollback()
            return None
    
    def get_booking(self, booking_id: int) -> Optional[Booking]:
        """
        Retrieve a specific booking by ID.
        
        MODIFY HERE: Add additional filtering or data transformation
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_booking(row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get booking {booking_id}: {e}")
            return None
    
    def get_bookings_by_date(self, date: str) -> List[Booking]:
        """
        Get all bookings for a specific date.
        
        MODIFY HERE: Add sorting or filtering options
        """
        try:
            normalized_date = self._normalize_date(date)
            if not normalized_date:
                logger.error(f"Invalid date format: {date}")
                return []
            
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM bookings 
                WHERE appointment_date = ? AND status != 'cancelled'
                ORDER BY appointment_time
            """, (normalized_date,))
            
            rows = cursor.fetchall()
            return [self._row_to_booking(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get bookings for date {date}: {e}")
            return []
    
    def get_bookings_by_phone(self, phone: str) -> List[Booking]:
        """
        Get all bookings for a specific phone number.
        
        MODIFY HERE: Add date range filtering or status filtering
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM bookings 
                WHERE customer_phone = ?
                ORDER BY appointment_date DESC, appointment_time DESC
            """, (phone.strip(),))
            
            rows = cursor.fetchall()
            return [self._row_to_booking(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get bookings for phone {phone}: {e}")
            return []
    
    def is_time_slot_booked(self, date: str, time: str) -> bool:
        """
        Check if a specific time slot is already booked.
        
        MODIFY HERE: Add buffer time or service-specific duration checking
        """
        try:
            normalized_date = self._normalize_date(date)
            normalized_time = self._normalize_time(time)
            
            if not normalized_date or not normalized_time:
                return True  # Assume booked if we can't parse the date/time
            
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM bookings 
                WHERE appointment_date = ? AND appointment_time = ? 
                AND status != 'cancelled'
            """, (normalized_date, normalized_time))
            
            count = cursor.fetchone()[0]
            return count > 0
            
        except Exception as e:
            logger.error(f"Failed to check time slot availability: {e}")
            return True  # Assume booked on error for safety
    
    def update_booking_status(self, booking_id: int, new_status: str) -> bool:
        """
        Update the status of a booking.
        
        MODIFY HERE: Add status validation or additional status types
        """
        try:
            # Validate status
            valid_statuses = ['confirmed', 'cancelled', 'completed', 'no-show']
            if new_status not in valid_statuses:
                logger.error(f"Invalid booking status: {new_status}")
                return False
            
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE bookings 
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (new_status, datetime.now(), booking_id))
            
            if cursor.rowcount > 0:
                self.connection.commit()
                logger.info(f"Booking {booking_id} status updated to {new_status}")
                return True
            else:
                logger.warning(f"No booking found with ID {booking_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update booking status: {e}")
            self.connection.rollback()
            return False
    
    def cancel_booking(self, booking_id: int) -> bool:
        """
        Cancel a booking (sets status to cancelled).
        
        MODIFY HERE: Add cancellation policies or notification logic
        """
        return self.update_booking_status(booking_id, 'cancelled')
    
    def get_available_time_slots(self, date: str, service_name: str = "") -> List[str]:
        """
        Get available time slots for a specific date.
        
        MODIFY HERE: Customize business hours or time slot intervals
        """
        try:
            # Define business hours and time slots
            # MODIFY HERE: Change business hours or time intervals
            business_hours = {
                'start': 9,   # 9 AM
                'end': 17,    # 5 PM
                'interval': 60  # 60 minutes between slots
            }
            
            # Generate all possible time slots
            all_slots = []
            current_hour = business_hours['start']
            
            while current_hour < business_hours['end']:
                # Format time as "HH:MM AM/PM"
                if current_hour == 0:
                    time_str = "12:00 AM"
                elif current_hour < 12:
                    time_str = f"{current_hour}:00 AM"
                elif current_hour == 12:
                    time_str = "12:00 PM"
                else:
                    time_str = f"{current_hour - 12}:00 PM"
                
                all_slots.append(time_str)
                current_hour += business_hours['interval'] // 60
            
            # Get booked slots for the date
            booked_bookings = self.get_bookings_by_date(date)
            booked_times = [booking.appointment_time for booking in booked_bookings]
            
            # Filter out booked slots
            available_slots = [slot for slot in all_slots if slot not in booked_times]
            
            return available_slots
            
        except Exception as e:
            logger.error(f"Failed to get available time slots: {e}")
            return []
    
    def get_booking_statistics(self) -> Dict[str, Any]:
        """
        Get booking statistics for reporting.
        
        MODIFY HERE: Add more statistics or change reporting period
        """
        try:
            cursor = self.connection.cursor()
            
            # Total bookings
            cursor.execute("SELECT COUNT(*) FROM bookings")
            total_bookings = cursor.fetchone()[0]
            
            # Bookings by status
            cursor.execute("""
                SELECT status, COUNT(*) 
                FROM bookings 
                GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())
            
            # Bookings by service
            cursor.execute("""
                SELECT service_name, COUNT(*) 
                FROM bookings 
                GROUP BY service_name
                ORDER BY COUNT(*) DESC
            """)
            service_counts = dict(cursor.fetchall())
            
            # Recent bookings (last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT COUNT(*) FROM bookings 
                WHERE created_at >= ?
            """, (thirty_days_ago,))
            recent_bookings = cursor.fetchone()[0]
            
            return {
                'total_bookings': total_bookings,
                'status_breakdown': status_counts,
                'service_breakdown': service_counts,
                'recent_bookings_30_days': recent_bookings,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get booking statistics: {e}")
            return {}
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """
        Normalize date string to YYYY-MM-DD format.
        
        MODIFY HERE: Add more date formats or change default format
        """
        try:
            # Handle natural language dates
            today = datetime.now()
            date_lower = date_str.lower().strip()
            
            if date_lower in ['today']:
                return today.strftime('%Y-%m-%d')
            elif date_lower in ['tomorrow']:
                return (today + timedelta(days=1)).strftime('%Y-%m-%d')
            elif 'next week' in date_lower:
                return (today + timedelta(days=7)).strftime('%Y-%m-%d')
            
            # Try to parse various date formats
            date_formats = [
                '%Y-%m-%d',      # 2024-01-15
                '%m/%d/%Y',      # 01/15/2024
                '%d/%m/%Y',      # 15/01/2024
                '%B %d, %Y',     # January 15, 2024
                '%b %d, %Y',     # Jan 15, 2024
                '%B %d',         # January 15 (current year)
                '%b %d'          # Jan 15 (current year)
            ]
            
            for fmt in date_formats:
                try:
                    if '%Y' not in fmt:
                        # Add current year for formats without year
                        date_str_with_year = f"{date_str} {today.year}"
                        parsed_date = datetime.strptime(date_str_with_year, f"{fmt} %Y")
                    else:
                        parsed_date = datetime.strptime(date_str, fmt)
                    
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse date: {date_str}")
            return None
            
        except Exception as e:
            logger.error(f"Error normalizing date {date_str}: {e}")
            return None
    
    def _normalize_time(self, time_str: str) -> Optional[str]:
        """
        Normalize time string to consistent format.
        
        MODIFY HERE: Change time format or add more time parsing patterns
        """
        try:
            time_lower = time_str.lower().strip()
            
            # Handle various time formats
            time_formats = [
                '%I:%M %p',      # 2:00 PM
                '%I %p',         # 2 PM
                '%H:%M',         # 14:00
                '%H'             # 14
            ]
            
            for fmt in time_formats:
                try:
                    parsed_time = datetime.strptime(time_str, fmt)
                    # Return in 12-hour format with AM/PM
                    return parsed_time.strftime('%I:%M %p').lstrip('0')
                except ValueError:
                    continue
            
            # Handle special cases
            if 'noon' in time_lower:
                return '12:00 PM'
            elif 'midnight' in time_lower:
                return '12:00 AM'
            
            logger.warning(f"Could not parse time: {time_str}")
            return None
            
        except Exception as e:
            logger.error(f"Error normalizing time {time_str}: {e}")
            return None
    
    def _row_to_booking(self, row) -> Booking:
        """
        Convert database row to Booking object.
        
        MODIFY HERE: Add new fields or change data transformation
        """
        return Booking(
            id=row['id'],
            customer_name=row['customer_name'],
            customer_phone=row['customer_phone'],
            customer_email=row['customer_email'] or "",
            service_name=row['service_name'],
            appointment_date=row['appointment_date'],
            appointment_time=row['appointment_time'],
            status=row['status'],
            notes=row['notes'] or "",
            google_calendar_event_id=row['google_calendar_event_id'] or "",
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
    
    def close(self):
        """
        Close database connection.
        
        MODIFY HERE: Add cleanup logic if needed
        """
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def __del__(self):
        """Destructor to ensure database connection is closed."""
        self.close()

# ===== UTILITY FUNCTIONS =====
def create_test_bookings(db: BookingDatabase) -> None:
    """
    Create some test bookings for development/testing.
    
    MODIFY HERE: Change test data or add more test scenarios
    """
    test_bookings = [
        {
            'customer_name': 'John Smith',
            'customer_phone': '555-0101',
            'customer_email': 'john.smith@email.com',
            'service_name': 'AI Calling Agent',
            'appointment_date': 'tomorrow',
            'appointment_time': '10:00 AM',
            'notes': 'Interested in automated customer service'
        },
        {
            'customer_name': 'Sarah Johnson',
            'customer_phone': '555-0102',
            'customer_email': 'sarah.j@email.com',
            'service_name': 'WhatsApp Business Automation',
            'appointment_date': 'tomorrow',
            'appointment_time': '2:00 PM',
            'notes': 'Small business owner, needs messaging automation'
        },
        {
            'customer_name': 'Mike Wilson',
            'customer_phone': '555-0103',
            'customer_email': 'mike.wilson@email.com',
            'service_name': 'Booking System',
            'appointment_date': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'appointment_time': '11:00 AM',
            'notes': 'Restaurant owner, needs online reservation system'
        }
    ]
    
    for booking_data in test_bookings:
        booking_id = db.add_booking(**booking_data)
        if booking_id:
            logger.info(f"Created test booking: {booking_id}")
        else:
            logger.warning(f"Failed to create test booking for {booking_data['customer_name']}")

# ===== MAIN FUNCTION FOR TESTING =====
def main():
    """
    Test the booking database functionality.
    
    MODIFY HERE: Add more test scenarios or change test behavior
    """
    print("🗄️ Vertiqx Booking Database - Test Mode")
    print("=" * 50)
    
    # Initialize database
    db = BookingDatabase("test_bookings.db")
    
    # Create test bookings
    print("\n📝 Creating test bookings...")
    create_test_bookings(db)
    
    # Test availability checking
    print("\n🔍 Testing availability checking...")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    available_slots = db.get_available_time_slots(tomorrow)
    print(f"Available slots for tomorrow: {available_slots}")
    
    # Test booking retrieval
    print("\n📋 Testing booking retrieval...")
    tomorrow_bookings = db.get_bookings_by_date(tomorrow)
    print(f"Bookings for tomorrow: {len(tomorrow_bookings)}")
    for booking in tomorrow_bookings:
        print(f"  - {booking.customer_name} at {booking.appointment_time} for {booking.service_name}")
    
    # Test statistics
    print("\n📊 Getting booking statistics...")
    stats = db.get_booking_statistics()
    print(f"Statistics: {json.dumps(stats, indent=2)}")
    
    # Close database
    db.close()
    print("\n✅ Database test completed successfully!")

if __name__ == "__main__":
    main()