import pandas as pd
import os
import requests
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import sqlite3
from datetime import datetime

# Set up logging for tracking alerts in the terminal
logging.basicConfig(level=logging.INFO)

# Load API key and email credentials
load_dotenv(r".env")
API_KEY = os.getenv('GROQ_API_KEY')
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

# Groq API URL for LLaMA 3.3 model
API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Prompt template for LLM analysis (unchanged)
PROMPT = """
You are a helpful assistant analyzing hotel reviews and guest preferences. The review below contains guest feedback and preference details. Analyze the feedback, correlate it with guest preferences, and determine if the sentiment is positive, neutral, or negative. Provide a personalized and empathetic response tailored for the guest.

Examples:
Positive Feedback Example:
Feedback: The spa was amazing, and the staff were very polite.
Preferences: Wellness
Response: Thank you for appreciating our wellness services! We're glad that you enjoyed your stay. Next time, consider trying our yoga sessions to enhance your wellness experience.

Negative Feedback Example:
Feedback: The room was dirty, and the AC didn't work.
Preferences: Room Preferences, Maintenance
Response: We sincerely apologize for the inconvenience caused by room cleanliness and AC issues. We've shared your feedback with our housekeeping and maintenance teams. As a gesture of goodwill, we'd like to offer a free room upgrade during your next stay.

Neutral Feedback Example:
Feedback: The check-in process was okay, but it could be faster.
Preferences: General
Response: Thank you for your feedback! We're always looking to improve our check-in experience.Feel free to use our express check-in feature for a quicker process next time.

Review: {review_text}
Preferences: {preferences}
Sentiment and Response:
"""

# Function to send email alerts
def send_email_alert(to_email, subject, body):
    """
    Sends an email alert to the specified email address.
    """
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
        print(f"Email alert sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"Failed to send email alert: {e}")
        return False

# Function to analyze review and generate sentiment, response, and department alert
def analyze_review_with_alert(review_text, preferences):
    """
    Uses LLM to analyze a review and generate sentiment, response, and department alert.
    """
    prompt = PROMPT.format(review_text=review_text, preferences=", ".join(preferences))

    messages = [{"role": "user", "content": prompt}]
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 750,
        "n": 1
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    # send POST request to the groq API for inference
    response = requests.post(API_URL, headers=headers, json=data)

    if response.status_code == 200:
        result_text = response.json()["choices"][0]["message"]["content"]

        sentiment = "Negative" if "apologize" in result_text else ("Positive" if "thank you" in result_text.lower() else "Neutral")

        # Generate department alert if sentiment is negative
        alert = None
        if sentiment == "Negative":
            alert = extract_department_alert_llm(review_text)
            if alert:
                email_body = f"Alert: {alert}\n\nReview: {review_text}"
                send_email_alert("anweshab018@gmail.com", "Negative Review Alert", email_body)
                send_slack_alert(f"Negative review alert: {alert}\n\nReview: {review_text}")

        return sentiment, result_text.strip(), alert

    else:
        print(f"Error {response.status_code}: {response.json()}")
        return None, None, None

# Function to log sentiment analysis to the Reviews table
def log_sentiment(guest_id, review, sentiment, suggestion):
    try:
        conn = sqlite3.connect("hotel_database.db")
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO Reviews (Guest_ID, Review, Sentiment, Suggestion)
        VALUES (?, ?, ?, ?)
        ''', (guest_id, review, sentiment, suggestion))
        conn.commit()
        print(f"[LOG] Sentiment logged: Guest_ID={guest_id}, Sentiment={sentiment}, Suggestion={suggestion}")
    except sqlite3.Error as e:
        print(f"[ERROR] Unable to log sentiment: {e}")
    finally:
        conn.close()
        
# Function to extract department responsible for negative feedback using LLM
def extract_department_alert_llm(review_text):
    """
    Uses LLM to identify the department responsible for addressing feedback.
    """
    prompt = f"""
You are an assistant tasked with identifying the department responsible for addressing guest feedback based on the review below. Analyze the feedback and provide the specific department name (e.g., Dining, Sports, Wellness, etc.).

Feedback: {review_text}
Department Responsible:
"""
    messages = [{"role": "user", "content": prompt}]
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 40,
        "n": 1
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(API_URL, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        print(f"Error {response.status_code}: {response.json()}")
        return "General feedback - Further investigation needed."

# Function to log interactions
def log_interaction(guest_id, activity, rating=None, time_spent=None):
    """
    Logs a guest's interaction in the Interactions table.
    """
    try:
        conn = sqlite3.connect("hotel_database.db")
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO Interactions (Guest_ID, Activity, Rating, Time_Spent, Timestamp)
        VALUES (?, ?, ?, ?, ?)
        ''', (guest_id, activity, rating, time_spent, datetime.now()))
        conn.commit()
        logging.info(f"[LOG] Interaction logged: Guest_ID={guest_id}, Activity={activity}, Rating={rating}, Time_spent={time_spent}, Timestamp={datetime.now()}")
    except sqlite3.Error as e:
        logging.error(f"[ERROR] Failed to log interaction: {e}")
    finally:
        conn.close()

# Function to send department-specific emails
def send_department_email(department, subject, message):
    """
    Sends an email to a specific department.
    """
    department_email = f"{department.lower()}@amethystestate.com"
    return send_email_alert(department_email, subject, message)

# Function to send Slack alerts
def send_slack_alert(message):
    """
    Sends an alert to Slack for negative reviews.
    """
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json={"text": message})
        response.raise_for_status()
        print("Slack alert sent successfully")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Slack alert: {e}")
        return False

# Main execution (for testing purposes)
if __name__ == "__main__":
    # Test the sentiment analysis and alert system
    test_review = "The room was dirty and the service was terrible."
    test_preferences = ["Room Preference: Clean", "Service: Excellent"]
    sentiment, response, alert = analyze_review_with_alert(test_review, test_preferences)
    print(f"Sentiment: {sentiment}")
    print(f"Response: {response}")
    print(f"Alert: {alert}")

    # Test sending a department email
    send_department_email("Housekeeping", "Room Cleanliness Complaint", "A guest reported that their room was not properly cleaned. Please investigate and take necessary action.")

    # Test logging an interaction
    log_interaction("G0001", "Spa Visit", rating=5, time_spent=120)

    print("Test execution completed.")

