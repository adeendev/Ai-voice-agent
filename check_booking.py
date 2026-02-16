import sqlite3

conn = sqlite3.connect('vertiqx_bookings.db')
cursor = conn.cursor()

# Check all recent bookings
cursor.execute('SELECT * FROM bookings ORDER BY created_at DESC LIMIT 5')
bookings = cursor.fetchall()

print("Recent bookings:")
for booking in bookings:
    print(f"ID: {booking[0]}, Name: {booking[1]}, Service: {booking[4]}, Date: {booking[5]}, Time: {booking[6]}, Booking ID: {booking[9]}")

# Check for specific booking ID
cursor.execute('SELECT * FROM bookings WHERE booking_id LIKE "%VTX-20251102211406%"')
specific_booking = cursor.fetchone()

if specific_booking:
    print(f"\nFound booking VTX-20251102211406:")
    print(f"Time stored: {specific_booking[6]}")
    print(f"Full record: {specific_booking}")
else:
    print("\nBooking VTX-20251102211406 not found")

conn.close()