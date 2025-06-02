import google.generativeai as genai
import os
import streamlit as st 

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", None)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY) 
else:
    # Display error if API key is missing
    st.error("LLM Service Critical Error: GEMINI_API_KEY environment variable not set. The AI features will not work.")


def call_gemini_api(prompt: str, history: list) -> str:
    """
    Calls the Google Gemini API with a given prompt and conversation history.

    Args:
        prompt (str): The user's prompt or question.
        history (list): A list of dictionaries representing the conversation history for the API.
                        Each dictionary should have "role" ("user" or "model") and "parts" (list of {"text": "message"}).
                        For this app, history is often [] as prompts are self-contained.

    Returns:
        str: The response text from the Gemini API.

    Raises:
        ValueError: If GEMINI_API_KEY is not effectively set (though initial check tries to prevent this).
        Exception: For other API-related errors if not caught and re-raised as a string.
    """
    if not GEMINI_API_KEY:
        # If genai.configure wasn't called.
        return "AI service is not configured. Please ensure GEMINI_API_KEY is set."

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-001') 
        
        # Format the history for the API call to {"role": "user/model", "parts": [{"text": "message"}]}
        formatted_history = []
        for msg in history:
            role = "user" if msg["sender"] == "user" else "model"
            formatted_history.append({"role": role, "parts": [{"text": msg["message"]}]})

        contents_for_api = formatted_history + [{"role": "user", "parts": [{"text": prompt}]}]
        
        generation_config = genai.types.GenerationConfig()

        response = model.generate_content(
            contents_for_api,
            generation_config=generation_config
            )

        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        elif response.prompt_feedback and response.prompt_feedback.block_reason:
            block_reason = response.prompt_feedback.block_reason
            block_message = f"AI response blocked. Reason: {block_reason}."
            if response.prompt_feedback.safety_ratings:
                block_message += f" Safety Ratings: {response.prompt_feedback.safety_ratings}"
            st.warning(f"LLM Service: {block_message}")
            return f"I'm sorry, my response was blocked due to: {block_reason}. Please try rephrasing your input."
        else:
            st.warning("LLM Service: Gemini API returned an empty or malformed response.")
            return "I'm sorry, I couldn't generate a response. The AI model returned an unexpected reply."

    except Exception as e:
        error_str = str(e).lower()
        st.error(f"LLM Service: Error calling Gemini API: {e}")
        if "api key not valid" in error_str or "permission denied" in error_str:
            return "There's an issue with the AI service configuration (API key). Please contact support."
        elif "rate limit" in error_str:
            return "The AI service is experiencing high traffic. Please try again in a moment."
        elif "blocked" in error_str or "safety" in error_str: # General safety block
            return "My response was blocked due to safety guidelines. Please try rephrasing your input."
        elif "resource exhausted" in error_str:
             return "The AI service is currently overloaded. Please try again later."
        # Fallback for other errors
        return f"An unexpected error occurred while communicating with the AI: {e}. Please try again."