import sqlite3
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from sklearn.feature_extraction.text import TfidfVectorizer

def fetch_hotel_data(database_path):
    try:
        with sqlite3.connect(database_path) as conn:
            guest_preferences = pd.read_sql_query("SELECT * FROM Preferences", conn)
            hotel_activities = pd.read_sql_query("SELECT * FROM Activities", conn)
            guest_interactions = pd.read_sql_query("SELECT * FROM Interactions", conn)
        return guest_preferences, hotel_activities, guest_interactions
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None, None, None

def clean_and_normalize_data(guest_preferences, hotel_activities, guest_interactions):
    guest_preferences = guest_preferences.replace("No Preference", 0).fillna(0)

    for col in guest_preferences.columns[1:]:
        if guest_preferences[col].dtype == "object":
            guest_preferences[col] = guest_preferences[col].apply(lambda x: 0 if x == "0" else hash(str(x)) % 1000)

    scaler = MinMaxScaler()
    guest_preferences.iloc[:, 1:] = scaler.fit_transform(guest_preferences.iloc[:, 1:])

    if not guest_interactions.empty and 'Rating' in guest_interactions.columns and 'Time_Spent' in guest_interactions.columns:
        guest_interactions[["Rating", "Time_Spent"]] = scaler.fit_transform(guest_interactions[["Rating", "Time_Spent"]])

    return guest_preferences, hotel_activities, guest_interactions

def create_activity_vectors(hotel_activities):
    if hotel_activities.empty:
        raise ValueError("Activities data is empty. Please check your database.")

    tfidf = TfidfVectorizer()
    category_vectors = tfidf.fit_transform(hotel_activities['Category']).toarray()

    scaler = MinMaxScaler()
    numeric_features = scaler.fit_transform(hotel_activities[["Rating", "Time_Spent"]])

    hotel_activities["vector"] = [
        np.concatenate([cat_vec, num_feat])
        for cat_vec, num_feat in zip(category_vectors, numeric_features)
    ]

    return hotel_activities

def get_personalized_recommendations(guest_id, guest_preferences, hotel_activities, guest_interactions):
    guest_data = guest_preferences.loc[guest_preferences["Guest_ID"] == guest_id]
    if guest_data.empty:
        return []

    guest_vector = guest_data.iloc[:, 1:].values.flatten()
    activity_vector_size = len(hotel_activities.iloc[0]["vector"])
    
    if len(guest_vector) < activity_vector_size:
        guest_vector = np.pad(guest_vector, (0, activity_vector_size - len(guest_vector)))
    elif len(guest_vector) > activity_vector_size:
        guest_vector = guest_vector[:activity_vector_size]

    completed_activities = set(hotel_activities[hotel_activities["Guest_ID"] == guest_id]["Activity"])
    
    recommendations = []
    for _, activity in hotel_activities.iterrows():
        if activity["Activity"] not in completed_activities:
            activity_vector = np.array(activity["vector"])
            similarity = cosine_similarity([guest_vector], [activity_vector])[0][0]
            recommendations.append((activity["Activity"], similarity))

    return sorted(recommendations, key=lambda x: x[1], reverse=True)

def find_similar_guests(guest_id, hotel_activities):
    activity_matrix = pd.pivot_table(
        hotel_activities,
        values="Rating",
        index="Guest_ID",
        columns="Activity",
        fill_value=0
    )

    if guest_id not in activity_matrix.index:
        return []

    similarity_scores = pd.DataFrame(
        cosine_similarity(activity_matrix),
        index=activity_matrix.index,
        columns=activity_matrix.index
    )

    similar_guests = similarity_scores.loc[guest_id].sort_values(ascending=False).index[1:6]

    guest_activities = set(hotel_activities[hotel_activities["Guest_ID"] == guest_id]["Activity"])
    recommendations = set()

    for similar_guest in similar_guests:
        similar_guest_activities = set(hotel_activities[hotel_activities["Guest_ID"] == similar_guest]["Activity"])
        recommendations.update(similar_guest_activities - guest_activities)

    return list(recommendations)

def generate_recommendations(guest_id, guest_preferences, hotel_activities, guest_interactions):
    content_based_recs = get_personalized_recommendations(guest_id, guest_preferences, hotel_activities, guest_interactions)
    collaborative_recs = find_similar_guests(guest_id, hotel_activities)

    all_recommendations = {rec[0]: rec[1] for rec in content_based_recs}
    for rec in collaborative_recs:
        all_recommendations.setdefault(rec, 0)

    top_recommendations = sorted(all_recommendations.items(), key=lambda x: x[1], reverse=True)[:2]

    if top_recommendations:
        activities = ", ".join(rec[0] for rec in top_recommendations)
        return f"Hey, would you like to try our {activities}?"
    else:
        # Get a list of all available activities
        all_activities = hotel_activities['Activity'].tolist()
        if all_activities:
            # Randomly select up to 3 activities
            sample_size = min(3, len(all_activities))
            random_activities = np.random.choice(all_activities, size=sample_size, replace=False)
            activities_str = ", ".join(random_activities)
            return f"Discover something new! How about trying {activities_str}?"
        else:
            return "Explore our wide range of exciting activities and events!"

# Example usage
if __name__ == "__main__":
    db_path = "hotel_database.db"
    preferences, activities, interactions = fetch_hotel_data(db_path)
    if all((preferences is not None, activities is not None, interactions is not None)):
        print("Data fetched successfully.")
        preferences, activities, interactions = clean_and_normalize_data(preferences, activities, interactions)
        print("Data cleaned and normalized.")
        activities = create_activity_vectors(activities)
        print("Activity vectors created.")
        guest_id = "G0001"  # Example guest ID
        print(f"Generating recommendations for guest {guest_id}...")
        recommendations = generate_recommendations(guest_id, preferences, activities, interactions)
        print("Recommendations:")
        print(recommendations)
    else:
        print("Error: Unable to fetch data from the database.")

