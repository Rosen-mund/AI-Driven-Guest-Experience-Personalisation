import pandas as pd
import numpy as np
from faker import Faker
import random
from collections import defaultdict

def load_and_clean_data(file_path):
    data = pd.read_csv(file_path)
    print("Initial data shape:", data.shape)
    print("Missing values:\n", data.isnull().sum())
    
    fake = Faker()
    data['reviewed_by'] = data['reviewed_by'].fillna(lambda _: fake.name())
    data['reviewed_at'] = data['reviewed_at'].fillna('Unknown')
    
    nationalities = ['American', 'British', 'Canadian', 'Indian', 'Australian']
    data['nationality'] = data['nationality'].fillna(lambda _: random.choice(nationalities))
    
    data['hotel_name'] = data['hotel_name'].fillna('Unknown Hotel')
    data['tags'] = data['tags'].fillna('No tags')
    
    data = data.dropna(subset=['rating', 'review_text', 'review_title'])
    
    columns_to_drop = ['images', 'crawled_at', 'url', 'hotel_name', 'hotel_url', 'avg_rating', 'raw_review_text', 'meta']
    data = data.drop(columns=columns_to_drop)
    
    print("Cleaned data shape:", data.shape)
    print("Remaining missing values:\n", data.isnull().sum())
    
    return data

def generate_unique_email(name, email_counts):
    if pd.notnull(name):
        clean_name = name.lower().replace(" ", ".")
        email_counts[clean_name] += 1
        return f"{clean_name}{email_counts[clean_name]}@example.com"
    return "unknown@example.com"

def add_customer_email(data):
    email_counts = defaultdict(int)
    data['customer_email'] = data['reviewed_by'].apply(lambda name: generate_unique_email(name, email_counts))
    return data

def add_preference_columns(data):
    preference_columns = ['Dining', 'Sports', 'Wellness', 'Payment Options', 'Events', 'Room Preference', 'Pricing']
    for column in preference_columns:
        data[column] = 'Not Specified'
    return data, preference_columns

def assign_preferences(row, preference_details, fallback_preferences):
    for column, keywords in preference_details.items():
        for keyword, detail in keywords:
            if keyword in str(row['review_text']).lower() or keyword in str(row['review_title']).lower():
                row[column] = detail
                break
        if row[column] == 'Not Specified':
            row[column] = random.choice(fallback_preferences[column])
    return row

def introduce_no_preference(row, preference_columns):
    columns_to_alter = random.sample(preference_columns, k=random.randint(0, len(preference_columns)))
    for column in columns_to_alter:
        row[column] = "No Preference"
    return row

def add_additional_columns(data):
    data['Membership Status'] = data['Pricing'].apply(lambda x: random.choice(
        ['Golden Membership', 'Platinum Membership'] if 'luxury' in x else 
        ['Silver Membership', 'No Membership']))
    data['Customer Age'] = data['Pricing'].apply(lambda x: random.randint(30, 50) if 'luxury' in x else random.randint(25, 40))
    data['Total Guests'] = data['Pricing'].apply(lambda _: random.choices(range(1, 11), weights=[70, 20, 5, 3, 2] + [0.2]*5, k=1)[0])
    return data

def main():
    input_file = "booking_reviews copy.csv"
    output_file = "updated_with_preferences_and_no_preference.csv"
    
    data = load_and_clean_data(input_file)
    data = add_customer_email(data)
    
    data, preference_columns = add_preference_columns(data)
    
    preference_details = {
        'Dining': [('vegan', 'vegan menu'), ('vegetarian', 'vegetarian options'), ('breakfast', 'complimentary breakfast')],
        'Sports': [('gym', 'gym access'), ('swimming', 'swimming pool'), ('tennis', 'tennis court')],
        'Wellness': [('spa', 'spa treatments'), ('relaxing', 'relaxing environment'), ('massage', 'massage services')],
        'Payment Options': [('card', 'card payments'), ('cash', 'cash only'), ('wallet', 'digital wallets')],
        'Events': [('wedding', 'wedding arrangements'), ('conference', 'conference rooms'), ('party', 'party halls')],
        'Room Preference': [('suite', 'suite room'), ('balcony', 'room with balcony'), ('ocean', 'ocean view')],
        'Pricing': [('expensive', 'luxury'), ('cheap', 'budget-friendly'), ('value', 'value for money')]
    }
    
    fallback_preferences = {
        'Dining': ['vegan menu', 'continental breakfast', 'dinner buffet'],
        'Sports': ['gym access', 'swimming pool', 'tennis court'],
        'Wellness': ['spa treatments', 'relaxing environment', 'yoga classes'],
        'Payment Options': ['card payments', 'digital wallets', 'cash only'],
        'Events': ['wedding arrangements', 'party halls', 'conference facilities'],
        'Room Preference': ['suite room', 'ocean view', 'room with balcony'],
        'Pricing': ['luxury', 'value for money', 'budget-friendly']
    }
    
    data = data.apply(lambda row: assign_preferences(row, preference_details, fallback_preferences), axis=1)
    data = data.apply(lambda row: introduce_no_preference(row, preference_columns), axis=1)
    
    data = add_additional_columns(data)
    
    data.to_csv(output_file, index=False)
    print(f"Updated dataset saved to {output_file}")

if __name__ == "__main__":
    main()
