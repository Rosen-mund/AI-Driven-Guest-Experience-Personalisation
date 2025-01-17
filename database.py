import sqlite3
import pandas as pd #for using hotel review dataset

# Creates a database file named 'hotel_database.db'
conn = sqlite3.connect("hotel_database.db")

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

print("Database connected successfully!")

# Create Guest Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Guests (
    Guest_ID TEXT PRIMARY KEY,
    Name TEXT NOT NULL,
    Email TEXT NOT NULL
)
''')
# Drop the existing Preferences table
cursor.execute("DROP TABLE IF EXISTS Preferences")
# Create Preferences Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Preferences (
    Guest_ID TEXT PRIMARY KEY,
    Dining TEXT,
    Sports TEXT,
    Wellness TEXT,
    Room_Preference TEXT,
    Pricing TEXT,
    FOREIGN KEY (Guest_ID) REFERENCES Guests (Guest_ID)
)
''')

# Create Review Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Reviews (
    Review_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Guest_ID TEXT,
    Review TEXT,
    Sentiment TEXT,
    Suggestion TEXT,
    FOREIGN KEY (Guest_ID) REFERENCES Guests (Guest_ID)
)
''')

cursor.execute("DROP TABLE IF EXISTS Activities")
cursor.execute('''
CREATE TABLE IF NOT EXISTS Activities (
    Activity_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Guest_ID TEXT,
    Activity TEXT,
    Category TEXT,
    Rating INTEGER,
    Time_Spent INTEGER,
    Date DATE,
    Time_Of_Day TEXT,
    FOREIGN KEY (Guest_ID) REFERENCES Guests (Guest_ID)
)
''')

# Create Interaction Table
cursor.execute("DROP TABLE IF EXISTS Interactions")
cursor.execute('''
CREATE TABLE Interactions (
    Interaction_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Guest_ID TEXT,
    Activity TEXT NOT NULL,
    Rating INTEGER,
    Time_Spent INTEGER,
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Guest_ID) REFERENCES Guests (Guest_ID)
)
''')
conn.commit()
print("Interactions table created.")


print("Tables created successfully!")
cursor.execute("DELETE FROM Guests")
cursor.execute("DELETE FROM Preferences")
cursor.execute("DELETE FROM Reviews")
cursor.execute("DELETE FROM Interactions")
cursor.execute("DELETE FROM Activities")
conn.commit()

dataset_path = r"updated_with_preferences_and_no_preference.csv" 
df = pd.read_csv(dataset_path)

# Take the first 100 rows
df = df.head(100)

#Insert data into Guests table
for index, row in df.iterrows():
    cursor.execute('''
    INSERT INTO Guests (Guest_ID, Name, Email)
    VALUES (?, ?, ?)
    ''', (f'G{index+1:04}', row['reviewed_by'], row['customer_email']))

# Insert data into Preferences table
for index, row in df.iterrows():
    cursor.execute('''
    INSERT INTO Preferences (Guest_ID, Dining, Sports, Wellness, Room_Preference, Pricing)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        f'G{index+1:04}',
        row['Dining'], row['Sports'], row['Wellness'],
        row['Room Preference'], row['Pricing']
    ))

conn.commit()
print("Data inserted successfully!")

# Query Guests Table for testing purpose
cursor.execute("SELECT * FROM Guests LIMIT 5")
for row in cursor.fetchall():
    print(row)

# Query Preferences Table
cursor.execute("SELECT * FROM Preferences LIMIT 5")
for row in cursor.fetchall():
    print(row)

#adding mock interaction data for testing 
activities = [
    ("G0001", "gym", 5, 60),
    ("G0002", "swimming", 4, 45),
    ("G0003", "spa", 5, 90)
]

for activity in activities:
    cursor.execute('''
    INSERT INTO Interactions (Guest_ID, Activity, Rating, Time_Spent)
    VALUES (?, ?, ?, ?)
    ''', activity)

conn.commit()
print("Interactions added successfully!")

# Query and print the Guests table
print("Guests Table:")
cursor.execute("SELECT * FROM Guests")
for row in cursor.fetchall():
    print(row)

# Query and print the Preferences table
print("\nPreferences Table:")
cursor.execute("SELECT * FROM Preferences")
for row in cursor.fetchall():
    print(row)

# Query and print the Interactions table
print("\nInteractions Table:")
cursor.execute("SELECT * FROM Interactions")
for row in cursor.fetchall():
    print(row)



conn.close()
print("Database closed!")

    








