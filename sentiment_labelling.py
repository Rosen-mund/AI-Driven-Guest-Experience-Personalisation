import os
import requests
import logging
import smtplib
import sqlite3
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv(".env")
API_KEY = os.getenv('GROQ_API_KEY')
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))

# API Configuration
API_URL = "https://api.groq.com/openai/v1/chat/completions"
PROMPT_TEMPLATE = """
You are a helpful assistant analyzing hotel reviews and guest preferences. The review below contains guest feedback and preference details. Analyze the feedback, correlate it with guest preferences, and determine if the sentiment is positive, neutral, or negative. Provide a personalized and empathetic response tailored for the guest.

Examples:
Positive Feedback Example:
Feedback: The spa was amazing, and the staff were very polite.
Preferences: Wellness
Response: Thank you for appreciating our wellness services! We’re glad that you enjoyed your stay. Next time, consider trying our yoga sessions to enhance your wellness experience.

Negative Feedback Example:
Feedback: The room was dirty, and the AC didn’t work.
Preferences: Room Preferences, Maintenance
Response: We sincerely apologize for the inconvenience caused by room cleanliness and AC issues. We’ve shared your feedback with our housekeeping and maintenance teams. As a gesture of goodwill, we’d like to offer a free room upgrade during your next stay.

Neutral Feedback Example:
Feedback: The check-in process was okay, but it could be faster.
Preferences: General
Response: Thank you for your feedback! We’re always looking to improve our check-in experience. Feel free to use our express check-in feature for a quicker process next time.

Review: {review_text}
Preferences: {preferences}
Sentiment and Response:
"""

# Function to send email alerts
def send_email_alert(to_email, subject, body):
    """Sends an email alert."""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())
        logging.info(f"Email alert sent to {to_email}: {subject}")
    except Exception as e:
        logging.error(f"Failed to send email alert: {e}")

# Function to analyze a review
def analyze_review(review_text, preferences):
    """Analyze a review and determine sentiment, response, and alerts."""
    prompt = PROMPT_TEMPLATE.format(review_text=review_text, preferences=", ".join(preferences))

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 100,
        "n": 1
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"]

        # Determine sentiment
        sentiment = "Negative" if "apologize" in result.lower() else ("Positive" if "thank you" in result.lower() else "Neutral")
        return sentiment, result.strip()
    except Exception as e:
        logging.error(f"Error analyzing review: {e}")
        return None, None

# Function to log sentiment in the database
def log_sentiment(guest_id, review, sentiment, suggestion):
    """Log sentiment analysis results in the database."""
    try:
        cursor.execute('''
            INSERT INTO Reviews (Guest_ID, Review, Sentiment, Suggestion)
            VALUES (?, ?, ?, ?)
        ''', (guest_id, review, sentiment, suggestion))
        conn.commit()
        logging.info(f"Sentiment logged: Guest_ID={guest_id}, Sentiment={sentiment}")
    except sqlite3.Error as e:
        logging.error(f"Error logging sentiment: {e}")

# Function to process dataset
def process_reviews(dataset):
    """Process hotel reviews dataset."""
    dataset['sentiment'] = ''
    dataset['suggestion'] = ''
    
    for index, row in dataset.iterrows():
        review_text = row['review_text']
        preferences = [row[col].strip() for col in ['Dining', 'Sports', 'Wellness', 'Room Preference'] if pd.notna(row[col])]

        sentiment, response = analyze_review(review_text, preferences)
        if sentiment and response:
            dataset.at[index, 'sentiment'] = sentiment
            dataset.at[index, 'suggestion'] = response.split("Response:")[1].strip() if "Response:" in response else "No suggestion available"
            log_sentiment(f"G{index+1:04}", review_text, sentiment, dataset.at[index, 'suggestion'])

# Load dataset
dataset_path = "updated_with_preferences_and_no_preference.csv"
dataset = pd.read_csv(dataset_path).iloc[:5]
process_reviews(dataset)

# Save processed dataset
dataset.to_csv("Sentiment_updated_hotel_reviews_with_alerts.csv", index=False)
logging.info("Dataset processed and saved.")

# Close database connection
conn = sqlite3.connect("hotel_database.db", check_same_thread=False)
cursor = conn.cursor()
conn.close()
logging.info("Database connection closed.")
