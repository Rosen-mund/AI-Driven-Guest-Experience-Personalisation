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
from bs4 import BeautifulSoup

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

# Prompt for sentiment analysis
PROMPT = """
You are an attentive assistant specializing in analyzing hotel reviews and guest preferences. The review below provides feedback about the guest's experience and preferences during their stay. Analyze the feedback, determine the sentiment (positive, neutral, or negative), and craft a personalized, empathetic response. Address specific concerns, highlight positives, and suggest relevant improvements or future offerings based on their preferences.

Examples:

Positive Feedback Example:
Feedback: The staff was extremely courteous, and the rooftop pool had breathtaking views.
Preferences: Hospitality, Amenities
Response: Thank you for your kind feedback! We're delighted that you enjoyed our hospitality and the rooftop pool. We'd love to welcome you back soon for another memorable experience.

Negative Feedback Example:
Feedback: The room was noisy, and the restaurant service was very slow.
Preferences: Room Preferences, Dining Experience
Response: We sincerely apologize for the noise disturbance and delays in restaurant service. Your concerns have been shared with our team to ensure improvements. To make up for this, we'd like to offer you a discount on your next stay.

Neutral Feedback Example:
Feedback: The room was nice, but the gym equipment could use an upgrade.
Preferences: Room Comfort, Fitness Facilities
Response: Thank you for sharing your feedback! We're happy to hear you liked the room. We're currently evaluating upgrades to our gym equipment and hope to offer an improved fitness experience soon.

Review: {review_text}
Preferences: {preferences}
Sentiment and Response:
"""

def send_email_alert(to_email, subject, body):
    """
    Sends an email alert to the specified email address.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())
        print(f"Email alert sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"Failed to send email alert: {e}")
        return False

def analyze_review_with_alert(review_text, preferences, guest_id):
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

        # Generate alert for both positive and negative reviews
        alert = extract_department_alert_llm(review_text)
        recommendations = generate_recommendations(guest_id)
        
        email_body = create_alert_message(sentiment, alert, review_text, recommendations)
        send_email_alert("springboardmentor543@gmail.com", f"{sentiment.upper()} Review Alert", email_body)
        send_slack_alert(email_body)

        return sentiment, result_text.strip(), alert

    else:
        print(f"Error {response.status_code}: {response.json()}")
        return None, None, None

def create_alert_message(sentiment, alert, review_text, recommendations):
    """
    Creates an HTML formatted alert message including recommendations.
    """
    color = "#FF0000" if sentiment == "Negative" else "#03b323"
    importance = "High" if sentiment == "Negative" else "Normal"
    
    recommendation_html = ""
    if recommendations['status'] == 'success':
        recommendation_html = f"<h3>{recommendations['message']}</h3><ul>"
        for rec in recommendations['recommendations']:
            recommendation_html += f"<li><strong>{rec['activity']}</strong> ({rec['category']}): {rec['description']}</li>"
        recommendation_html += "</ul>"
    else:
        recommendation_html = f"<p>{recommendations['message']}</p>"
    
    message = f"""
    <html>
    <body>
    <h2 style='color: {color};'>New {sentiment} Review</h2>
    <p><strong>Importance:</strong> {importance}</p>
    <p><strong>Department:</strong> {alert}</p>
    <p><strong>Review:</strong> {review_text}</p>
    <h3>Recommendations for the guest:</h3>
    {recommendation_html}
    </body>
    </html>
    """
    return message

def log_sentiment(guest_id, review, sentiment, suggestion):
    """
    Logs the sentiment analysis results to the database.
    """
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

def send_slack_alert(message):
    """
    Sends an alert to Slack for reviews.
    """
    try:
        soup = BeautifulSoup(message, 'html.parser')
        plain_text = soup.get_text()
        
        # Format the plain text for better readability in Slack
        formatted_text = ""
        for line in plain_text.split('\n'):
            line = line.strip()
            if line.endswith(':'):
                formatted_text += f"*{line}*\n"
            elif line.startswith('•'):
                formatted_text += f"  • {line[1:].strip()}\n"
            else:
                formatted_text += f"{line}\n"
        
        response = requests.post(SLACK_WEBHOOK_URL, json={"text": formatted_text})
        response.raise_for_status()
        print("Slack alert sent successfully")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Slack alert: {e}")
        return False

def generate_recommendations(guest_id):
    """
    Generates personalized recommendations based on guest preferences.
    """
    try:
        conn = sqlite3.connect("hotel_database.db")
        cursor = conn.cursor()
        
        # Fetch guest preferences
        cursor.execute("SELECT * FROM Preferences WHERE Guest_ID = ?", (guest_id,))
        preferences = cursor.fetchone()
        
        if not preferences:
            return {
                'status': 'no_activities',
                'message': 'We recommend trying our spa services and joining our guided nature walks.'
            }
            
        dining = preferences[1]
        sports = preferences[2]
        wellness = preferences[3]
        
        recs = []
        # Only add recommendations for preferences that exist and aren't empty/null
        if dining and dining.strip():
            recs.append({
                'activity': 'Dining',
                'category': 'Restaurant',
                'description': f"Try our {dining} restaurant"
            })
        if sports and sports.strip():
            recs.append({
                'activity': 'Sports',
                'category': 'Activity',
                'description': f"Join our {sports} activities"
            })
        if wellness and wellness.strip():
            recs.append({
                'activity': 'Wellness',
                'category': 'Treatment',
                'description': f"Experience our {wellness} treatments"
            })
        
        if recs:
            return {
                'status': 'success',
                'message': 'Based on your preferences, we recommend:',
                'recommendations': recs
            }
        else:
            # Return default message if no valid preferences were found
            return {
                'status': 'no_activities',
                'message': 'We recommend trying our spa services and joining our guided nature walks.'
            }
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return {
            'status': 'error',
            'message': 'We recommend trying our spa services and joining our guided nature walks.'
        }
    finally:
        conn.close()

if __name__ == "__main__":
    # Test the sentiment analysis and alert system
    test_review = "The room was dirty and the service was terrible."
    test_preferences = ["Room Preference: Clean", "Service: Excellent"]
    sentiment, response, alert = analyze_review_with_alert(test_review, test_preferences, "G0022")
    print(f"Sentiment: {sentiment}")
    print(f"Response: {response}")
    print(f"Alert: {alert}")

    # Test logging an interaction
    log_interaction("G0022", "Spa Visit", rating=5, time_spent=120)

    print("Test execution completed.")
