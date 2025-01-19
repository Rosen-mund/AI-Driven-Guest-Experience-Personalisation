import streamlit as st
import sqlite3
from sentiment_labelling import analyze_review_with_alert, log_sentiment, log_interaction
from recmdsys import generate_recommendations, fetch_hotel_data, clean_and_normalize_data, create_activity_vectors

# Sample user credentials (unchanged)
USER_DB = {
    "Jhondoe1@example.com": {"password": "password123", "Guest_ID": "G0001"},
    "joshep1@example.com": {"password": "password456", "Guest_ID": "G0002"},
    "seon1@example.com": {"password": "password150", "Guest_ID": "G0003"},
    "felix1@example.com": {"password": "password140", "Guest_ID": "G0014"},
    "anastesia1@example.com": {"password": "password220", "Guest_ID": "G0022"},
}

# Connect to SQLite database
conn = sqlite3.connect("hotel_database.db")
cursor = conn.cursor()

def set_page_config():
    st.set_page_config(page_title="The Amethyst Estate", layout="wide")
    st.markdown("""
        <style>
        .main {
            background-color: #f0f0f0;
        }
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        </style>
    """, unsafe_allow_html=True)

def header():
    st.title("The Amethyst Estate")

def sidebar():
    with st.sidebar:
        st.header("Navigation")
        page = st.radio("Go to", ["Login", "Feedback", "Profile Management"])
    return page

def login_form():
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if email in USER_DB and USER_DB[email]["password"] == password:
                st.session_state["logged_in"] = True
                st.session_state["user_email"] = email
                st.session_state["guest_id"] = USER_DB[email]["Guest_ID"]
                st.success(f"Welcome, {email}!")
            else:
                st.error("Invalid email or password!")

def feedback_form():
    st.subheader("Your Thoughts Are Valuable to Us")
    st.write(f"Logged in as: {st.session_state['user_email']} (Guest ID: {st.session_state['guest_id']})")

    review_input = st.text_area("Enter your review here")
    if st.button("Submit review"):
        if review_input.strip():
            preferences = {
                "dining": "Dinner buffet", "sports": "Swimming", "wellness": "Spa",
                "payment options": "Credit card", "events": "Wedding",
                "pricing": "Affordable", "room preferences": "Ocean view",
            }
            formatted_preferences = ", ".join(f"{key}: {value}" for key, value in preferences.items())
            sentiment, response, department = analyze_review_with_alert(review_input, formatted_preferences)
            log_sentiment(st.session_state["guest_id"], review_input, sentiment, response)
            st.session_state["review_submitted"] = True 
            st.success("Thank you! Your review has been submitted successfully.")
            st.info(response)
        else:
            st.error("Please enter a valid review!")

def display_ads():
    st.subheader("Browse Our Range of Activities")
    ads = [
        "Outdoor Adventure Gear", "Relaxation Spa Essentials", "Guided Yoga Sessions",
        "Thrilling Adventure Experience", "Holistic Wellness Escape", "Authentic Italian Dining",
        "Aquatic Adventure Bundle"
    ]
    
    for ad in st.columns(3):
        for item in ads[:3]:
            if ad.button(f"View {item}"):
                log_interaction(st.session_state["guest_id"], item, rating=None, time_spent=60)
                st.session_state["clicked_ads"][item] = True
                st.success(f"Click here to know more about {item}...")
        ads = ads[3:]

def show_recommendations():
    if st.session_state.get("review_submitted") and st.session_state.get("clicked_ads"):
        db_path = "hotel_database.db"
        preferences, activities, interactions = fetch_hotel_data(db_path)
        if all((preferences is not None, activities is not None, interactions is not None)):
            preferences, activities, interactions = clean_and_normalize_data(preferences, activities, interactions)
            activities = create_activity_vectors(activities)
            recommendations = generate_recommendations(
                st.session_state["guest_id"],
                preferences,
                activities,
                interactions
            )
            st.success(recommendations)
        else:
            st.error("Unable to fetch data from the database. Please try again later.")

def profile_management():
    st.subheader("Profile Management")
    guest_id = st.session_state["guest_id"]
    
    # Fetch current profile data
    cursor.execute("SELECT * FROM Guests WHERE Guest_ID = ?", (guest_id,))
    guest_data = cursor.fetchone()
    
    cursor.execute("SELECT * FROM Preferences WHERE Guest_ID = ?", (guest_id,))
    preferences_data = cursor.fetchone()
    
    if guest_data and preferences_data:
        with st.form("profile_form"):
            name = st.text_input("Name", value=guest_data[1])
            email = st.text_input("Email", value=guest_data[2])
            dining = st.text_input("Dining Preference", value=preferences_data[1])
            sports = st.text_input("Sports Preference", value=preferences_data[2])
            wellness = st.text_input("Wellness Preference", value=preferences_data[3])
            room_preference = st.text_input("Room Preference", value=preferences_data[4])
            pricing = st.text_input("Pricing Preference", value=preferences_data[5])
            
            if st.form_submit_button("Update Profile"):
                try:
                    cursor.execute("""
                        UPDATE Guests SET Name = ?, Email = ? WHERE Guest_ID = ?
                    """, (name, email, guest_id))
                    cursor.execute("""
                        UPDATE Preferences 
                        SET Dining = ?, Sports = ?, Wellness = ?, Room_Preference = ?, Pricing = ?
                        WHERE Guest_ID = ?
                    """, (dining, sports, wellness, room_preference, pricing, guest_id))
                    conn.commit()
                    st.success("Profile updated successfully!")
                except sqlite3.Error as e:
                    st.error(f"An error occurred: {e}")
    else:
        st.error("Unable to fetch profile data. Please try again later.")

def main():
    set_page_config()
    header()
    page = sidebar()

    if "clicked_ads" not in st.session_state:
        st.session_state["clicked_ads"] = {}

    if page == "Login" and not st.session_state.get("logged_in", False):
        login_form()
    elif not st.session_state.get("logged_in", False):
        st.warning("Please log in first.")
        login_form()
    else:
        if page == "Feedback":
            feedback_form()
            display_ads()
            show_recommendations()
        elif page == "Profile Management":
            profile_management()

if __name__ == "__main__":
    main()

