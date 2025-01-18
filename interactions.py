import sqlite3 
from sqlite3 import connect
from faker import Faker

faker = Faker()

dbPromise = connect('hotel_database.db')

activities = {
  'Relaxation': ['spa_treatment', 'meditation_session', 'aromatherapy', 'hot_stone_massage'],
  'Fitness': ['pilates', 'crossfit', 'aqua_aerobics', 'rock_climbing'],
  'Culinary': ['cooking_class', 'wine_tasting', 'sushi_making', 'farm_to_table_experience'],
  'Cultural': ['art_exhibition', 'local_market_tour', 'language_class', 'historical_walk'],
  'Adventure': ['zip_lining', 'scuba_diving', 'horseback_riding', 'paragliding']
}

async def generate_interactions(db, count=500):
    stmt = await db.execute('''
        INSERT INTO Interactions (Guest_ID, Activity, Rating, Time_Spent, Timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''')

    all_activities = [activity for sublist in activities.values() for activity in sublist]

    for _ in range(count):
        guest_id = f"G{faker.random_number(digits=4, fix_len=True)}"
        activity = faker.random.choice(all_activities)
        rating = faker.random_int(min=1, max=5)
        time_spent = faker.random_int(min=10, max=120)
        timestamp = faker.date_time_between(start_date='-30d', end_date='now')

        await stmt.execute((guest_id, activity, rating, time_spent, timestamp.isoformat()))

    await db.commit()
    print(f"{count} random interactions logged")


async def populate_activities(db, num_guests=100, min_activities=5, max_activities=10):
    stmt = await db.execute('''
        INSERT INTO Activities (Guest_ID, Activity, Category, Rating, Time_Spent, Date, Time_Of_Day)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''')

    start_date = faker.date_time_between(start_date='-30d', end_date='now')
    time_of_day_options = ['morning', 'afternoon', 'evening']

    for i in range(num_guests):
        guest_id = f"G{str(i + 1).zfill(4)}"
        num_activities = faker.random_int(min=min_activities, max=max_activities)

        for _ in range(num_activities):
            category = faker.random.choice(list(activities.keys()))
            activity = faker.random.choice(activities[category])
            rating = faker.random_int(min=1, max=5)
            time_spent = faker.random_int(min=30, max=180)
            date = faker.date_time_between(start_date=start_date, end_date='now')
            time_of_day = faker.random.choice(time_of_day_options)

            await stmt.execute((guest_id, activity, category, rating, time_spent, date.isoformat().split('T')[0], time_of_day))

    await db.commit()
    print("Activities table populated successfully!")


async def main():
    try:
        db = await dbPromise
        await generate_interactions(db)
        await populate_activities(db)
    except Exception as error:
        print("An error occurred:", error)
    finally:
        await db.close()

import asyncio
asyncio.run(main())
