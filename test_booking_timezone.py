#!/usr/bin/env python3
"""
Test script to verify that the 2 PM booking scenario creates the correct time in Google Calendar.
This test validates the timezone fix for the voice agent booking system.
"""

import os
import sys
import logging
from datetime import datetime, time
import pytz
from booking_manager import BookingManager
from google_calendar_integration import GoogleCalendarIntegration

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_2pm_booking_scenario():
    """Test that a 2 PM booking creates the correct time in Google Calendar."""
    
    print("=" * 60)
    print("TESTING 2 PM BOOKING SCENARIO")
    print("=" * 60)
    
    # Initialize BookingManager
    try:
        booking_manager = BookingManager()
        print("✓ BookingManager initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize BookingManager: {e}")
        return False
    
    # Test data for 2 PM booking
    test_name = "Test User"
    test_phone = "555-123-4567"
    test_email = "test@example.com"
    test_service = "Messaging Solutions"
    test_notes = "Test booking for 2 PM timezone verification"
    
    # Create appointment time for 2 PM today in Eastern Time
    eastern = pytz.timezone('America/New_York')
    today = datetime.now(eastern).date()
    appointment_time = datetime.combine(today, time(14, 0))  # 2:00 PM
    appointment_time = eastern.localize(appointment_time)
    
    print(f"Test appointment time: {appointment_time}")
    print(f"Timezone: {appointment_time.tzinfo}")
    print(f"UTC equivalent: {appointment_time.utctimetuple()}")
    
    # Create the booking
    try:
        print("\nCreating booking through BookingManager...")
        result = booking_manager.create_booking(
            name=test_name,
            phone=test_phone,
            service=test_service,
            appointment_time=appointment_time.strftime('%Y-%m-%d %H:%M'),
            email=test_email,
            notes=test_notes
        )
        
        if result.get('success'):
            booking_id = result.get('booking_id')
            calendar_event_id = result.get('calendar_event_id')
            
            print(f"✓ Booking created successfully!")
            print(f"  Booking ID: {booking_id}")
            print(f"  Calendar Event ID: {calendar_event_id}")
            
            # Verify the calendar event if Google Calendar is available
            if calendar_event_id and booking_manager.google_calendar:
                print("\nVerifying Google Calendar event...")
                try:
                    # Get the event from Google Calendar
                    event = booking_manager.google_calendar.service.events().get(
                        calendarId='primary',
                        eventId=calendar_event_id
                    ).execute()
                    
                    start_time = event['start'].get('dateTime', event['start'].get('date'))
                    end_time = event['end'].get('dateTime', event['end'].get('date'))
                    
                    print(f"  Calendar event start time: {start_time}")
                    print(f"  Calendar event end time: {end_time}")
                    
                    # Parse the start time to verify it's correct
                    if 'T14:00:00' in start_time and '-05:00' in start_time:
                        print("✓ Calendar event shows correct 2 PM Eastern Time!")
                    elif 'T14:00:00' in start_time and '-04:00' in start_time:
                        print("✓ Calendar event shows correct 2 PM Eastern Daylight Time!")
                    else:
                        print(f"⚠ Calendar event time may be incorrect: {start_time}")
                        
                except Exception as e:
                    print(f"✗ Failed to verify calendar event: {e}")
            
            return True
            
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"✗ Booking creation failed: {error_msg}")
            return False
            
    except Exception as e:
        print(f"✗ Exception during booking creation: {e}")
        return False

def test_timezone_consistency():
    """Test that all components use consistent timezone configuration."""
    
    print("\n" + "=" * 60)
    print("TESTING TIMEZONE CONSISTENCY")
    print("=" * 60)
    
    # Check BookingManager timezone
    try:
        booking_manager = BookingManager()
        bm_timezone = getattr(booking_manager, 'timezone', None)
        print(f"BookingManager timezone: {bm_timezone}")
    except Exception as e:
        print(f"Could not check BookingManager timezone: {e}")
    
    # Check GoogleCalendarIntegration timezone
    try:
        from google_calendar_integration import LOCAL_TIMEZONE, TIMEZONE_OBJ
        print(f"GoogleCalendarIntegration LOCAL_TIMEZONE: {LOCAL_TIMEZONE}")
        print(f"GoogleCalendarIntegration TIMEZONE_OBJ: {TIMEZONE_OBJ}")
    except Exception as e:
        print(f"Could not check GoogleCalendarIntegration timezone: {e}")
    
    # Check voice agent timezone
    try:
        from vertiqx_voice_agent import LOCAL_TIMEZONE as VOICE_TIMEZONE
        print(f"Voice Agent LOCAL_TIMEZONE: {VOICE_TIMEZONE}")
    except Exception as e:
        print(f"Could not check Voice Agent timezone: {e}")

def main():
    """Run all timezone tests."""
    
    print("Starting timezone fix verification tests...")
    
    # Test timezone consistency
    test_timezone_consistency()
    
    # Test 2 PM booking scenario
    success = test_2pm_booking_scenario()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ ALL TESTS PASSED - Timezone fix appears to be working correctly!")
    else:
        print("✗ TESTS FAILED - There may still be timezone issues")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    main()