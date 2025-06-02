# 🤖 TalentScout Hiring Assistant Chatbot

## Project Overview
The TalentScout Hiring Assistant is an AI-powered chatbot designed for initial candidate screening in tech recruitment. It efficiently gathers essential candidate information and generates personalized technical questions based on their declared tech stack, ensuring a streamlined and context-aware experience.

## Core Features:

* **Information Collection**: Gathers candidate's name, contact, location, experience, desired roles, and tech stack.
* **Dynamic Technical Assessment:** Generates 3 tailored technical questions using an LLM, based on the candidate's declared technologies.
* **Contextual Interaction:** Maintains conversation flow for coherent user experience and handles general follow-up questions.
* **Profile Management:** Allows candidates to review and submit their collected data to a Firebase backend.

## Purpose of Prompting
Effective prompt engineering guides the Large Language Model (LLM) to:

* **Gather Information:** Collect candidate details accurately and conversationally.
* **Generate Questions:** Create specific, relevant technical questions from the tech stack.
* **Maintain Context:** Ensure coherent interactions and appropriate responses to general queries, staying within the chatbot's role.

## Installation Instructions
To run the chatbot locally, follow these steps:

## Setup
**Clone Repository:**
```Bash

git clone <your-repository-url>
cd <your-repository-name>
```
**Create Virtual Environment & Install Dependencies:**
```Bash

python -m venv venv
# On Windows: .\venv\Scripts\activate
# On macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```
**Set Environment Variables:**
* **GEMINI_API_KEY:** Your Google Gemini API key from Google AI Studio.
* **FIREBASE_CONFIG_B64:** Base64 encoded content of your Firebase service account JSON file. (Refer to detailed README version for how to encode the JSON.)
* Store these in a .env file (add .env to .gitignore).

**Run Application:**
```Bash

streamlit run app.py
```
## Usage Guide
* **Start:** Chatbot greets you and asks for your name.
* **Input Details:** Follow prompts to provide your name, email, location, phone number, years of experience, and desired position.
* **Declare Tech Stack:** Enter your primary tech stack (e.g., "Python, React, AWS").
* **Technical Assessment:** Type "OK" or "Yes" to begin 3 technical questions. Provide your answers for each.
* **Submit Profile:** Review your information on the left panel, then click "✅ Save and Submit Profile".
* **Follow-up:** Ask general questions about the hiring process.
* **Exit:** Type exit or quit to end the conversation.

## Technical Details
* **Frontend:** Streamlit (app.py, style.css)
* **LLM:** Google Gemini (gemini-2.0-flash-001) via llm_service.py
* **Backend:** Google Firebase Firestore via firebase_service.py
* **Modular Design:** Separates UI logic (app.py), LLM interaction (llm_service.py), and database operations (firebase_service.py) for maintainability.
* **State Management:** st.session_state is used to persist conversational context and candidate data across Streamlit reruns.

## Prompt Design Highlights
Prompts are designed to guide the LLM for specific outcomes:

* **Technical Questions:** Instructs LLM to act as an interviewer, generate 3 concise questions based on provided tech stack, focusing on fundamentals.
* **Contextual Responses:** Guides the LLM to respond helpfully to general queries (e.g., about hiring process, profile status) while maintaining its role as a hiring assistant and gracefully declining out-of-scope questions.

## Challenges & Solutions
* **Context in Streamlit:** Managed using st.session_state to store and retrieve conversation history and candidate data.
* **LLM Dual Purpose:** Implemented distinct prompts and conditional logic in app.py to handle both structured data collection and open-ended queries.
* **Asynchronous Operations:** Used st.session_state.is_loading and st.session_state.pending_operation flags to manage UI state during LLM calls and database saves, preventing race conditions.
* **Secure Credentials:** Ensured API keys and Firebase config are loaded via environment variables (and Base64 encoded for Firebase JSON).

## Deliverables
* **Documentation:** This README.md file.
* **Demo:** [[Link ](https://talent-scout-chatbot.streamlit.app/)]
