# AI DRIVEN GUEST EXPERIENCE PERSONALISATION
The AI-Driven Guest Experience Personalization System is a cutting-edge solution to revolutionize how hotels enhance guest satisfaction and loyalty. This project incorporates LLMS to deliver an unmatched personalized experience for each guest. The system is built on three core functionalities: dynamic profile management, real-time sentiment analysis of hotel reviews, and a personalized recommendation system.
## Key Features
1. Realtime Sentiment Analysis of Hotel Reviews
   - By leveraging LLMS, the system processes guest reviews in real time to gauge customer sentiment.
   - It identifies key issues and positive highlights, allowing hotel management to act on negative feedback and reinforce positive experiences immediately.
2. Personalized Recommendation System
      - The recommendation system engine uses AI to analyze guest profiles and sentiment insights to provide curated suggestions for room preferences, spa treatments, and dining options.
      - By aligning with individual guest preferences, the system ensures an exceptional and personalized stay.
3. Dynamic Profile Management
   - The System creates and updates comprehensive guest profiles dynamically, capturing their preferences, past interactions, booking history, and behavioral patterns.
   - These profiles enable hotels to understand guests on a deeper level and offer tailored services such as room upgrades, dining suggestions, and leisure activities.
## Instruction to set up Project locally
### Installation
1. Clone Repository
   ```
   git clone https://github.com/Rosen-mund/AI-Driven-Guest-Experience-Personalisation
   ```
2. Create a virtual environment (Windows user)
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install Dependencies
   ```
   pip install -r requirements.txt
   ```
4. Create .env file to enter api key from Groq Cloud, email id, email app key , and slack web hook url.
## Project Structure
- guest_ui.py - Frontend for user interaction
- stentiment_labelling.py - Backend dedicated to sentiment analysis, Email and slack bot integration
- recmdsys.py - Backend to handle Recommendation Algorithms
- main.py - Backend to handle the dataset. Used for removing unwanted columns, handling missing values etc.
- database.py - Used for Dynamic profile handleing
## Technology Stack
  - Python(3.12.0)
  - Pandas, ScikitLearn
  - SMPT for handling email alerts
  - Sqlite3
  - Groq API key
  - LLM (llama-3.3-70b-versatile)
  - Streamlit
## System WorkFlow 
![mermaid-diagram-2025-01-19-153310](https://github.com/user-attachments/assets/54c3faa8-c56f-4a1a-a2bf-454151609e4a)


   
   
