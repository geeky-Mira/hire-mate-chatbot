# 🤖 HireMate — AI-Powered Hiring Assistant Chatbot

## 🧭 Overview

**HireMate** is an AI-driven hiring assistant chatbot designed to automate **initial candidate screening** in tech recruitment. It interacts conversationally to collect candidate data, generate **personalized technical questions** based on the declared tech stack, and store responses in a Firebase backend — making the hiring process smarter, faster, and more consistent.

---

## 🚀 Core Features

* **🗂️ Smart Data Collection:** Gathers candidate's name, contact, location, experience, desired roles, and tech stack.
* **🧠 Dynamic Technical Assessment:** Generates 3 tailored technical questions using an LLM, based on the candidate's declared technologies.
* **💬 Contextual Interaction:** Maintains conversation flow for coherent user experience and handles general follow-up questions.
* **☁️ Profile Management:** Allows candidates to review and submit their collected data to a Firebase backend.

---

## 🎯 Purpose of Prompting

Effective prompt engineering guides the Large Language Model (LLM) to:

* **Gather Information:** Collect candidate details accurately and conversationally.
* **Generate Questions:** Create specific, relevant technical questions from the tech stack.
* **Maintain Context:** Ensure coherent interactions and appropriate responses to general queries, staying within the chatbot's role.

---

## ⚙️ Installation & Setup

To run the chatbot locally, follow these steps:

### 1️⃣ Clone Repository

```bash
git clone https://github.com/geeky-Mira/talent-scout-chatbot.git
cd talent-scout-chatbot
```

### 2️⃣ Create Virtual Environment & Install Dependencies

```bash
python -m venv venv
# On Windows: .\venv\Scripts\activate
# On macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 3️⃣ Set Environment Variables

* **GEMINI_API_KEY:** Your Google Gemini API key from Google AI Studio.
* **FIREBASE_CONFIG_B64:** Base64 encoded content of your Firebase service account JSON file.
  *(Refer to detailed README for encoding instructions.)*
* Store these in a `.env` file (and add `.env` to `.gitignore`).

### 4️⃣ Run Application

```bash
streamlit run app.py
```

---

## 💡 Usage Guide

* **Start:** Chatbot greets you and asks for your name.
* **Input Details:** Provide name, email, location, phone, years of experience, and desired position.
* **Declare Tech Stack:** Enter your primary stack (e.g., "Python, React, AWS").
* **Technical Assessment:** Type `OK` or `Yes` to begin 3 technical questions and respond to each.
* **Submit Profile:** Review details on the left panel, then click **✅ Save and Submit Profile**.
* **Follow-up:** Ask questions about the hiring process or your submission.
* **Exit:** Type `exit` or `quit` to end the session.

---

## 🧱 Technical Details

* **Frontend:** Streamlit (`app.py`, `style.css`)
* **LLM Engine:** Google Gemini (`gemini-2.0-flash-001`) via `llm_service.py`
* **Backend:** Firebase Firestore via `firebase_service.py`
* **Architecture:** Modular separation for UI, LLM, and backend layers.
* **State Management:** `st.session_state` persists conversation data across Streamlit reruns.

---

## 🧠 Prompt Design Highlights

Prompts are carefully structured to guide the LLM for specific outcomes:

* **Technical Questions:** Directs the model to act as a hiring interviewer, generating concise, stack-specific questions focusing on fundamentals.
* **Contextual Responses:** Guides the chatbot to handle general or clarifying questions gracefully while maintaining its role.

---

## 🛠️ Challenges & Solutions

* **Context Retention in Streamlit:** Managed via `st.session_state` to store and reuse chat history.
* **Dual-Purpose LLM:** Used distinct prompt templates and conditional logic in `app.py` for structured vs open-ended conversations.
* **Async Operations:** Flags like `is_loading` and `pending_operation` manage UI state and prevent race conditions during async LLM/database calls.
* **Secure Credentials:** API keys and Firebase configs handled via environment variables (Firebase JSON Base64 encoded).

---

## 📦 Deliverables

* **Documentation:** `README.md`
* **Live Demo:** [HireMate Chatbot](https://hire-mate-chatbot.streamlit.app/)

---

## 👩‍💻 Author

**Developed by:** [@geeky-Mira](https://github.com/geeky-Mira)
Empowering intelligent automation through conversational AI.

---
