import pandas as pd
import numpy as np
import faker
import random
from collections import defaultdict

# Load the dataset
data = pd.read_csv(r"booking_reviews copy.csv")
print(data.head())
#checking for missing values
print(data.isnull().sum())

# Create a Faker object to generate random names
fake = faker.Faker()

# Load your dataset
data = pd.read_csv(r"booking_reviews copy.csv")

# Check for missing values in the 'reviewed_by' column
print(data['reviewed_by'].isnull().sum())  

# Replace missing values in 'reviewed_by' with random names
data['reviewed_by'] = data['reviewed_by'].apply(lambda x: x if pd.notnull(x) else fake.name())

# Verify the changes
print(data[['reviewed_by', 'review_text']].head())  # Check the first few rows

print(data.isnull().sum())

# Fill missing 'reviewed_at' values with 'Unknown'
data['reviewed_at'] = data['reviewed_at'].fillna('Unknown')

# List of nationalities
nationalities = ['American', 'British', 'Canadian', 'Indian', 'Australian']
# Fill missing 'nationality' values with random nationality from the list
data['nationality'] = data['nationality'].apply(lambda x: random.choice(nationalities) if pd.isnull(x) else x)

# Fill missing 'hotel_name' values with 'Unknown Hotel'
data['hotel_name'] = data['hotel_name'].fillna('Unknown Hotel')

# Fill missing 'tags' values with 'No tags'
data['tags'] = data['tags'].fillna('No tags')

# Drop rows where 'rating' or 'review_text' is missing
data = data.dropna(subset=['rating', 'review_text'])

# Verify the changes
print(data[['rating', 'review_text']].head()) 

# Drop the specified columns
columns_to_drop = ['images', 'crawled_at', 'url','hotel_name', 'hotel_url', 'avg_rating', 'raw_review_text', 'meta']
data.drop(columns=columns_to_drop, inplace=True)
data = data.dropna(subset=['review_title'])

# Verify the changes by checking the columns
print(data.columns)
# Check for missing values in the dataset
missing_values = data.isnull().sum()

# Display the number of missing values per column
print(missing_values)

# Save the updated dataset to a new CSV file
data.to_csv('cleaned_booking_reviews.csv', index=False)

# Load your dataset
data = pd.read_csv("cleaned_booking_reviews.csv")

# Initialize a defaultdict to track email counts for duplicates
email_counts = defaultdict(int)

# Function to generate unique email IDs
def generate_unique_email(name):
    if pd.notnull(name):  # Check if name is not null
        clean_name = name.lower().replace(" ", ".") 
        email_counts[clean_name] += 1  # Increment the count for this name
        return f"{clean_name}{email_counts[clean_name]}@example.com"  # Append count and domain
    return "unknown@example.com"  # Default for missing names

# Apply the function to create the email column
data['customer_email'] = data['reviewed_by'].apply(generate_unique_email)

# Replace NaN or float values with an empty string
data['review_text'] = data['review_text'].fillna('')

# Save the updated dataset to a new CSV file
data.to_csv("cleaned_booking_reviews_v2.csv", index=False)

# Display first few rows to verify
print(data[['reviewed_by', 'customer_email']].head())


# Load the updated dataset
dataset_path = "cleaned_booking_reviews_v2.csv"
df = pd.read_csv(dataset_path)

# Add new preference columns with default values (e.g., 'Not Specified')
preference_columns = ['Dining', 'Sports', 'Wellness', 'Payment Options', 'Events', 'Room Preference', 'Pricing']
for column in preference_columns:
    df[column] = 'Not Specified'  # Default value for new columns
print(f"Preferences columns added successfully.")

#filling preference columns by analyzing review_text,review_title and ratings by using NLP and conditional logic to map value
# Define keyword mapping with specific details
preference_details = {
    'Dining': [('vegan', 'vegan menu'), ('vegetarian', 'vegetarian options'), ('breakfast', 'complimentary breakfast')],
    'Sports': [('gym', 'gym access'), ('swimming', 'swimming pool'), ('tennis', 'tennis court')],
    'Wellness': [('spa', 'spa treatments'), ('relaxing', 'relaxing environment'), ('massage', 'massage services')],
    'Payment Options': [('card', 'card payments'), ('cash', 'cash only'), ('wallet', 'digital wallets')],
    'Events': [('wedding', 'wedding arrangements'), ('conference', 'conference rooms'), ('party', 'party halls')],
    'Room Preference': [('suite', 'suite room'), ('balcony', 'room with balcony'), ('ocean', 'ocean view')],
    'Pricing': [('expensive', 'luxury'), ('cheap', 'budget-friendly'), ('value', 'value for money')]
}
# Fallback random values for missing preferences
fallback_preferences = {
    'Dining': ['vegan menu', 'continental breakfast', 'dinner buffet'],
    'Sports': ['gym access', 'swimming pool', 'tennis court'],
    'Wellness': ['spa treatments', 'relaxing environment', 'yoga classes'],
    'Payment Options': ['card payments', 'digital wallets', 'cash only'],
    'Events': ['wedding arrangements', 'party halls', 'conference facilities'],
    'Room Preference': ['suite room', 'ocean view', 'room with balcony'],
    'Pricing': ['luxury', 'value for money', 'budget-friendly']
}


# Function to assign preferences based on reviews
def assign_preferences(row):
    for column, keywords in preference_details.items():
        # Check if keywords match in review text or title
        for keyword, detail in keywords:
            if keyword in str(row['review_text']).lower() or keyword in str(row['review_title']).lower():
                row[column] = detail  # Assign specific detail
                break
        # If no match, assign a random fallback value
        if row[column] == 'Not Specified':
            row[column] = random.choice(fallback_preferences[column])
    return row

# Apply the function to fill preferences
df = df.apply(assign_preferences, axis=1)

# Randomly introduce "No Preference" in some cells
def introduce_no_preference(row):
    # Randomly decide how many and which columns to set to "No Preference"
    columns_to_alter = random.sample(preference_columns, k=random.randint(0, len(preference_columns)))
    for column in columns_to_alter:
        row[column] = "No Preference"
    return row

# Apply the function to introduce "No Preference"
df = df.apply(introduce_no_preference, axis=1)

# Add new columns and fill them with values
df['Membership Status'] = df['Pricing'].apply(lambda x: random.choice(
    ['Golden Membership', 'Platinum Membership'] if 'luxury' in x else 
    ['Silver Membership', 'No Membership']))

df['Customer Age'] = df['Pricing'].apply(lambda x: random.randint(30, 50) if 'luxury' in x else random.randint(25, 40))
df['Total Guests'] = df['Pricing'].apply(lambda _: random.choices(range(1, 11), weights=[70, 20, 5, 3, 2] + [0.2]*5, k=1)[0])

# Save the updated dataset
updated_dataset_path = "updated_with_preferences_and_no_preference.csv"
df.to_csv(updated_dataset_path, index=False)

print(f"Preferences updated with details and 'No Preference' introduced. Dataset saved to {updated_dataset_path}.")



