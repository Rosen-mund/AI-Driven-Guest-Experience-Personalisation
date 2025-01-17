import sqlite3
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from sklearn.feature_extraction.text import TfidfVectorizer

#Load Data from Database
def load_data_from_db(db_path):# database path provided while calling the function in the UI
    conn = sqlite3.connect(db_path)
    preferences_table = pd.read_sql_query("SELECT * FROM Preferences", conn)
    activities_table = pd.read_sql_query("SELECT * FROM Activities", conn)
    interaction_table = pd.read_sql_query("SELECT * FROM Interactions", conn)
    conn.close()
    return preferences_table, activities_table, interaction_table

# Preprocess Tables
def preprocess_tables(preferences_table, activities_table, interaction_table):
    preferences_table = preferences_table.replace("No Preference", 0).fillna(0)

    # Convert non-numeric preferences to numeric using hashing
    for column in preferences_table.columns[1:]:
        if preferences_table[column].dtype == "object":
            preferences_table[column] = preferences_table[column].apply(
                lambda x: 0 if x == "0" else hash(x) % 1000
            )

    # Normalize preferences
    scaler = MinMaxScaler()
    preferences_table.iloc[:, 1:] = scaler.fit_transform(preferences_table.iloc[:, 1:])

    # Normalize ratings and time spent
    interaction_table["Rating"] = MinMaxScaler().fit_transform(interaction_table[["Rating"]])
    interaction_table["Time_Spent"] = MinMaxScaler().fit_transform(interaction_table[["Time_Spent"]])

    return preferences_table, activities_table, interaction_table 
print(activities_table.head())  # To see the first few rows

# Generate Activity Embeddings
def generate_activity_embeddings(activities_table):
    if activities_table.empty:
        raise ValueError("Activities table is empty. Ensure it contains valid data.")

    # Using TF-IDF for category embeddings
    vectorizer = TfidfVectorizer()
    category_embeddings = vectorizer.fit_transform(activities_table['Category']).toarray()

    # Normalize numerical columns 
    scaler = MinMaxScaler()
    numerical_columns = ["Rating", "Time_Spent"]
    normalized_numerical = scaler.fit_transform(activities_table[numerical_columns])
    # Combine embeddings
    final_embeddings = []
    for i in range(len(activities_table)):
        combined = np.concatenate([category_embeddings[i], normalized_numerical[i]])
        final_embeddings.append(combined)

    activities_table["embedding"] = final_embeddings
    return activities_table

# Content-Based Recommendation
def content_based_recommendation(user_id, preferences_table, activities_table, interaction_table):
    user_row = preferences_table.loc[preferences_table["Guest_ID"] == user_id]
    if user_row.empty:
        return []
    user_preferences = user_row.iloc[:, 1:].values.flatten()

    # Padding user preferences to match activity embedding size
    embedding_size = len(activities_table.iloc[0]["embedding"])
    if len(user_preferences) != embedding_size:
        user_preferences = np.pad(user_preferences, (0, embedding_size - len(user_preferences)))

    recommendations = []
    completed_activities = activities_table[activities_table["Guest_ID"] == user_id]["Activity"].unique()


    for _, activity in activities_table.iterrows():
        if activity["Activity"] not in completed_activities:
            activity_embedding = np.array(activity["embedding"])
            similarity = cosine_similarity([user_preferences], [activity_embedding])[0][0]
            recommendations.append((activity["Activity"], similarity))

    recommendations.sort(key=lambda x: x[1], reverse=True)
    return recommendations

#Collaborative Filtering
def collaborative_filtering(user_id, activities_table):
    pivot_table = activities_table.pivot_table(
        index="Guest_ID",
        columns="Activity",
        aggfunc="size",  
        fill_value=0     # Fill missing values with 0 (activity not completed)
    )

    # Ensure the user exists in the pivot table
    if user_id not in pivot_table.index:
        return []

    # Calculate similarity matrix using cosine similarity
    similarity_matrix = cosine_similarity(pivot_table)
    similarity_df = pd.DataFrame(similarity_matrix, index=pivot_table.index, columns=pivot_table.index)
    similar_users = similarity_df.loc[user_id].sort_values(ascending=False).index[1:6]

    # Generate recommendations based on activities of similar users
    recommendations = set()
    user_activities = set(activities_table[activities_table["Guest_ID"] == user_id]["Activity"].unique())
    for similar_user in similar_users:
        similar_user_activities = set(activities_table[activities_table["Guest_ID"] == similar_user]["Activity"].unique())
        recommendations.update(similar_user_activities - user_activities)

    return list(recommendations)


# Combine Recommendations
def combined_recommendation(user_id, preferences_table, activities_table, interaction_table):
    content_recs = content_based_recommendation(user_id, preferences_table, activities_table, interaction_table)

    # Collaborative filtering recommendations (using the Activity Table)
    collab_recs = collaborative_filtering(user_id, activities_table)

    # Combine recommendations with scores
    combined_recs = {rec[0]: rec[1] for rec in content_recs}
    for rec in collab_recs:
        if rec not in combined_recs:
            combined_recs[rec] = 0 
    sorted_recommendations = sorted(combined_recs.items(), key=lambda x: x[1], reverse=True)
    top_recommendations = [rec[0] for rec in sorted_recommendations[:2]]

    if top_recommendations:
        return f"Hey, would you like to try our {', '.join(top_recommendations)}?"
    return "View our events and activities."





