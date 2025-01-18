import sqlite3
from datetime import datetime, timedelta

# Connect to the existing database
conn = sqlite3.connect("hotel_database.db")
cursor = conn.cursor()

# Fetch existing Guest_IDs
cursor.execute("SELECT Guest_ID FROM Guests")
guest_ids = [row[0] for row in cursor.fetchall()]

# Sample activities data
activities_data = [
    ("yoga", "Wellness", 4, 60, "morning"),
    ("swimming", "Sports", 5, 45, "afternoon"),
    ("spa", "Wellness", 5, 90, "evening"),
    ("tennis", "Sports", 4, 60, "morning"),
    ("gym", "Sports", 4, 45, "afternoon"),
    ("meditation", "Wellness", 5, 30, "morning")
]

# Generate sample data for Activities table
start_date = datetime.now().date()
for guest_id in guest_ids[:10]:  # Limit to first 10 guests for this example
    for _ in range(3):  # Each guest does 3 activities
        activity = activities_data[_ % len(activities_data)]
        date = start_date + timedelta(days=_)
        cursor.execute('''
        INSERT INTO Activities (Guest_ID, Activity, Category, Rating, Time_Spent, Date, Time_Of_Day)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (guest_id, activity[0], activity[1], activity[2], activity[3], date, activity[4]))

conn.commit()
print("Sample activities added successfully!")

# Query and print the Activities table
print("\nActivities Table:")
cursor.execute("SELECT * FROM Activities LIMIT 10")
for row in cursor.fetchall():
    print(row)

# Close the database connection
conn.close()

