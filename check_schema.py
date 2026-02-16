import sqlite3

conn = sqlite3.connect('vertiqx_bookings.db')
cursor = conn.cursor()

# Get table schema
cursor.execute("PRAGMA table_info(bookings)")
columns = cursor.fetchall()

print("Database schema:")
for col in columns:
    print(f"Column {col[0]}: {col[1]} ({col[2]})")

# Check all recent bookings with correct column names
cursor.execute('SELECT * FROM bookings ORDER BY created_at DESC LIMIT 3')
bookings = cursor.fetchall()

print("\nRecent bookings:")
for booking in bookings:
    print(f"Full record: {booking}")

conn.close()