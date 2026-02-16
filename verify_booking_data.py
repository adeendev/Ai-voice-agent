#!/usr/bin/env python3
"""
Script to verify that booking data is stored correctly in the database.
This checks the actual database records to ensure timezone handling is working.
"""

import sqlite3
from datetime import datetime
import pytz

def verify_booking_data():
    """Verify the booking data in the database."""
    
    print("=" * 60)
    print("VERIFYING BOOKING DATA IN DATABASE")
    print("=" * 60)
    
    try:
        # Connect to the database
        conn = sqlite3.connect("vertiqx_bookings.db")
        cursor = conn.cursor()
        
        # Get the most recent booking
        cursor.execute("""
            SELECT * FROM bookings 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        
        if row:
            print("Most recent booking found:")
            print(f"  ID: {row[0]}")
            print(f"  Customer Name: {row[1]}")
            print(f"  Customer Phone: {row[2]}")
            print(f"  Customer Email: {row[3]}")
            print(f"  Service Name: {row[4]}")
            print(f"  Appointment Date: {row[5]}")
            print(f"  Appointment Time: {row[6]}")
            print(f"  Status: {row[7]}")
            print(f"  Notes: {row[8]}")
            print(f"  Google Calendar Event ID: {row[9]}")
            print(f"  Created At: {row[10]}")
            print(f"  Updated At: {row[11]}")
            
            # Verify the appointment time is 14:00 (2 PM)
            appointment_time = row[6]
            if appointment_time == "14:00":
                print("\n✓ Appointment time correctly stored as 14:00 (2 PM)")
            else:
                print(f"\n⚠ Appointment time is {appointment_time}, expected 14:00")
            
            # Verify the appointment date is today
            appointment_date = row[5]
            today = datetime.now().strftime("%Y-%m-%d")
            if appointment_date == today:
                print(f"✓ Appointment date correctly stored as today ({today})")
            else:
                print(f"⚠ Appointment date is {appointment_date}, expected {today}")
                
        else:
            print("No bookings found in database")
            
        conn.close()
        
    except Exception as e:
        print(f"Error verifying booking data: {e}")

def check_all_bookings():
    """Display all bookings in the database."""
    
    print("\n" + "=" * 60)
    print("ALL BOOKINGS IN DATABASE")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect("vertiqx_bookings.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM bookings")
        count = cursor.fetchone()[0]
        print(f"Total bookings: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT id, customer_name, appointment_date, appointment_time, service_name, created_at
                FROM bookings 
                ORDER BY created_at DESC
            """)
            
            print("\nBooking Summary:")
            print("-" * 80)
            print(f"{'ID':<4} {'Name':<15} {'Date':<12} {'Time':<8} {'Service':<20} {'Created':<20}")
            print("-" * 80)
            
            for row in cursor.fetchall():
                created_at = row[5][:19] if row[5] else "N/A"  # Truncate timestamp
                print(f"{row[0]:<4} {row[1][:15]:<15} {row[2]:<12} {row[3]:<8} {row[4][:20]:<20} {created_at:<20}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking bookings: {e}")

if __name__ == "__main__":
    verify_booking_data()
    check_all_bookings()