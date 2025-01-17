import sqlite3
import random
import numpy as np
from datetime import datetime,timedelta

conn = sqlite3.connect(r"hotel_database.db")
cursor = conn.cursor()

def generate_interactions():
    activities = ["Spa Kit", "Yoga Class", "Adventure Package", "Wellness Retreat", "Hiking Gear","Italian cuisine","Water sports package"]
    guest_ids = [f"G{str(i).zfill(4)}" for i in range(1, 101)] 
    for _ in range(500):  # Generate 500 random interactions
        guest_id = random.choice(guest_ids)
        activity = random.choice(activities)
        rating = random.randint(1, 5)
        time_spent = np.random.randint(10, 120)

        # Log interaction
        cursor.execute('''
        INSERT INTO Interactions (Guest_ID, Activity, Rating, Time_Spent, Timestamp)
        VALUES (?, ?, ?, ?, ?)
        ''', (guest_id, activity, rating, time_spent, datetime.now()))
        conn.commit()
        print(" Random interaction logged")

# List of activities with their categories
activities = {
    'Wellness': ['spa', 'massage', 'yoga', 'meditation'],
    'Sports': ['gym', 'tennis', 'swimming', 'golf'],
    'Dining': ['buffet', 'room_service', 'fine_dining', 'cafe'],
    'Events': ['conference', 'wedding', 'party', 'workshop'],
    'Entertainment': ['movie_screening', 'live_music', 'game_room']
}

# activity data
def populate_activities(num_guests=100, min_activities=5, max_activities=10):
    start_date = datetime.now() - timedelta(days=30)  # Activities in the past 30 days
    time_of_day_options = ['morning', 'afternoon', 'evening']

    for guest_id in [f"G{str(i+1).zfill(4)}" for i in range(num_guests)]:
        num_activities = random.randint(min_activities, max_activities)
        for _ in range(num_activities):
            category = random.choice(list(activities.keys()))
            activity = random.choice(activities[category])
            rating = random.randint(1, 5)
            time_spent = random.randint(30, 180)  # Time spent in minutes
            date = start_date + timedelta(days=random.randint(0, 29))
            time_of_day = random.choice(time_of_day_options)

            # Insert into the table
            cursor.execute('''
            INSERT INTO Activities (Guest_ID, Activity, Category, Rating, Time_Spent, Date, Time_Of_Day)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (guest_id, activity, category, rating, time_spent, date.date(), time_of_day))

    conn.commit()
    print("Activities table populated successfully!")


if __name__ == "__main__":
    #populate_activities()
    generate_interactions()
