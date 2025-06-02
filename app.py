import streamlit as st
import json
import re
import os
st.set_page_config(page_title="TalentScout Hiring Assistant", layout="wide")
from llm_service import call_gemini_api 
from firebase_service import initialize_firebase, save_candidate_profile

from streamlit_phone_number import st_phone_number 

def format_history_for_prompt(chat_hist):
   return "\n".join([f"{msg['sender'].capitalize()}: {msg['message']}" for msg in chat_hist])

def main():
    # Load CSS 
    css_file_path = os.path.join("style.css")
    try:
        with open(css_file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Warning: style.css not found at {css_file_path}. Using default Streamlit styles.")
    except Exception as e:
        st.error(f"Error loading CSS: {e}")

    # Page Title
    st.title("🤖 TalentScout Hiring Assistant")

    # Firebase Configuration
    app_id = os.getenv('__app_id', 'talent-scout-app') 
    firebase_config_b64_str = os.getenv('FIREBASE_CONFIG_B64', '')
    initial_auth_token = os.getenv('__initial_auth_token', None)

    # Session State Initialization
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "candidate_info" not in st.session_state:
        st.session_state.candidate_info = {
            "fullName": "", "email": "", "currentLocation": "",
            "phoneNumber": "", "yearsExperience": "", "desiredPositions": "",
            "techStack": "", "technicalResponses": [], "saved_to_firestore": False
        }
    if "info_stage" not in st.session_state:
        st.session_state.info_stage = "name"
        st.session_state.chat_history.append(
            {"sender": "bot", "message": "Hello! Welcome to TalentScout’s Hiring Assistant. Please note: All data you provide will be used solely for this simulated hiring process and handled with care."}
        )
        st.session_state.chat_history.append(
            {"sender": "bot", "message": "May I have your full name? (You can type 'exit' anytime to end the conversation)"}
        )

    if "technical_questions" not in st.session_state:
        st.session_state.technical_questions = []
    if "current_question_index" not in st.session_state:
        st.session_state.current_question_index = 0
    if "is_loading" not in st.session_state:
        st.session_state.is_loading = False
    if "firebase_initialized" not in st.session_state:
        st.session_state.firebase_initialized = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "db" not in st.session_state:
        st.session_state.db = None
    if "auth" not in st.session_state:
        st.session_state.auth = None
    if "firebase_error" not in st.session_state:
        st.session_state.firebase_error = None
    if "current_user_input" not in st.session_state:
        st.session_state.current_user_input = None
    if "pending_operation" not in st.session_state:
        st.session_state.pending_operation = None
    if "position_selected_value" not in st.session_state:
        st.session_state.position_selected_value = None


    # Firebase Initialization
    if not st.session_state.firebase_initialized:
        st.session_state.db, st.session_state.auth, st.session_state.user_id, st.session_state.firebase_error = \
            initialize_firebase(app_id, firebase_config_b64_str, initial_auth_token)
        st.session_state.firebase_initialized = True
        if st.session_state.firebase_error:
            st.error(f"Firebase Initialization Error: {st.session_state.firebase_error}")
        st.rerun()

    
    # Layout: Two columns
    col1, col2 = st.columns([1, 2], gap="large")

    # Left Column: Candidate Information Panel
    with col1:
        st.markdown('<div class="candidate-info-panel">', unsafe_allow_html=True)
        st.subheader("Candidate Information")
        info = st.session_state.candidate_info
        if info["fullName"]: st.markdown(f"**Name:** {info['fullName']}")
        if info["email"]: st.markdown(f"**Email:** {info['email']}")
        if info["currentLocation"]: st.markdown(f"**Current Location:** {info['currentLocation']}")
        if info["phoneNumber"]: st.markdown(f"**Phone:** {info['phoneNumber']}")
        if info["yearsExperience"] != "": st.markdown(f"**Experience:** {info['yearsExperience']} years")
        if info["desiredPositions"]: st.markdown(f"**Desired Roles:** {info['desiredPositions']}")
        if info["techStack"]: st.markdown(f"**Tech Stack:** {info['techStack']}")
        if info["saved_to_firestore"]: st.success("Profile submitted and saved to database.")

        if (
            st.session_state.info_stage == "completed"
            and not info["saved_to_firestore"]
            and not st.session_state.is_loading
            and not st.session_state.pending_operation
        ):
            st.markdown("---")
            if st.button("✅ Save and Submit Profile", use_container_width=True, type="primary"):
                st.session_state.chat_history.append(
                    {"sender": "bot", "message": "Submitting your profile..."}
                )
                st.session_state.pending_operation = "save_profile"
                st.session_state.is_loading = True
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Right Column: Chat‐Style Interaction or Stage‐Specific Widgets
    with col2:
        st.subheader("Chat with TalentScout AI")
        chat_container = st.container(height=500, border=True)

        with chat_container:
            st.markdown(
                "<div class='chat-background-area' style='display: flex; flex-direction: column; "
                "height: 100%; overflow-y: auto;'>",
                unsafe_allow_html=True
            )
            for message_item in st.session_state.chat_history:
                if message_item["sender"] == "user":
                    st.markdown(
                        f'<div class="chat-message user-message">{message_item["message"]}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div class="chat-message bot-message">{message_item["message"]}</div>',
                        unsafe_allow_html=True
                    )
            st.markdown("</div>", unsafe_allow_html=True)


        stage = st.session_state.info_stage

        
        # Stage‐Specific Input Widgets
        if stage == "positions_select" and not st.session_state.is_loading and not st.session_state.pending_operation:
            job_options = [
                "Software Engineer", "Data Scientist", "Product Manager",
                "UX Designer", "DevOps Engineer", "Cloud Architect",
                "Cybersecurity Analyst", "Other"
            ]
            st.session_state.position_selected_value = st.selectbox(
                "Please choose your primary desired position from the list:",
                options=job_options,
                key="positions_selectbox_widget", 
                index=None,
                placeholder="Select a position..."
            )
        elif stage == "phoneNumber" and not st.session_state.is_loading and not st.session_state.pending_operation:
            st.write("Please enter your phone number:")
            st_phone_number(
                label="📱 Mobile Number",
                placeholder="(select country code via dropdown)",
                default_country="IN", 
                key="phone_number_widget" 
            )
            if st.button("Confirm Phone Number", key="confirm_phone_btn"):
                phone_value = st.session_state.get("phone_number_widget")
                if phone_value:
                    if isinstance(phone_value, dict): 
                        cc = phone_value.get("countryCallingCode", "")
                        national = phone_value.get("nationalNumber", "")
                        formatted_phone = f"+{cc} {national}".strip()
                        st.session_state.candidate_info["phoneNumber"] = formatted_phone
                    else: 
                        st.session_state.candidate_info["phoneNumber"] = phone_value
                    
                    st.session_state.chat_history.append({"sender": "user", "message": st.session_state.candidate_info["phoneNumber"]})
                    st.session_state.chat_history.append({"sender": "bot", "message": "Thank you. And how many years of professional experience do you have?"})
                    st.session_state.info_stage = "experience"
                    st.session_state.current_user_input = None
                    st.session_state.is_loading = False
                    st.rerun()
                else:
                    st.error("Please enter a valid phone number (e.g., +1 415-555-2671).")

        elif stage == "experience" and not st.session_state.is_loading and not st.session_state.pending_operation:
            st.write("Enter your years of professional experience (e.g., 0, 1, 5):")
            years = st.number_input(
                label="Years of Experience",
                min_value=0,
                step=1,
                key="experience_input_widget" 
            )
            if st.button("Confirm Experience", key="confirm_experience_btn"):
                st.session_state.candidate_info["yearsExperience"] = int(years)
                st.session_state.chat_history.append({"sender": "user", "message": str(years)})
                st.session_state.chat_history.append({"sender": "bot", "message": "Which primary job role are you interested in?"})
                st.session_state.info_stage = "positions_select"
                st.session_state.current_user_input = None
                st.session_state.is_loading = False
                st.rerun()
 
        
        if st.session_state.is_loading and stage not in ["exit", "final_confirmation", "completed"]:
            with st.spinner("Processing..."):
                pass 

        chat_input_disabled = (
            st.session_state.is_loading
            or st.session_state.pending_operation is not None
            or stage in [ 
                "positions_select", "phoneNumber", "experience", 
                "completed", "exit" 
            ]
        )

        if stage not in [
            "positions_select", "phoneNumber", "experience",
            "completed", "exit"
        ]:
            user_input_from_widget = st.chat_input(
                "Type your message here...", disabled=chat_input_disabled, key="main_chat_input_widget"
            )
            if user_input_from_widget:
                st.session_state.current_user_input = user_input_from_widget.strip()
                st.session_state.chat_history.append({"sender": "user", "message": st.session_state.current_user_input})
                st.session_state.is_loading = True 
                st.rerun() 
        elif chat_input_disabled:
             st.chat_input("Type your message here...", disabled=True, key="main_chat_input_widget_disabled")


        # Footer
        st.markdown(
            """
            <div style='position: relative; bottom: 0; width: 100%; text-align: left; padding-top: 20px;'>
                <p style='font-size: 0.75rem; color: #9CA3AF;'>&copy; 2024 TalentScout. Powered by Gemini & Firebase</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Handle Pending Operations (generate_questions, process_answer, save_profile)
    if st.session_state.pending_operation:
        op = st.session_state.pending_operation
        info = st.session_state.candidate_info

        if op == "generate_questions":
            try:
                prompt = (
                    f"You are a technical interviewer for TalentScout. "
                    f"Based on the tech stack: \"{info['techStack']}\", "
                    "generate exactly 3 concise and relevant technical questions. "
                    "Focus on fundamental concepts and practical application. "
                    "Format them as a numbered list (e.g., '1. Question one?', '2. Question two?')."
                )
                response_text = call_gemini_api(prompt, []) 
                questions = []
                for line in response_text.split('\n'):
                    match = re.match(r'^\s*\d+\.\s*(.*)$', line.strip())
                    if match:
                        questions.append(match.group(1).strip())

                st.session_state.technical_questions = questions[:3] 
                if st.session_state.technical_questions:
                    bot_msg = f"Okay, let's start with the first question: {st.session_state.technical_questions[0]}"
                    st.session_state.info_stage = "askingQuestion"
                    st.session_state.current_question_index = 0
                else:
                    bot_msg = "I had trouble generating questions based on your tech stack. Could you please try re-entering your tech stack with more specific terms or examples?"
                    st.session_state.info_stage = "techStack" 
                st.session_state.chat_history.append({"sender": "bot", "message": bot_msg})
            except Exception as e:
                st.error(f"Question generation error: {e}")
                st.session_state.chat_history.append({
                    "sender": "bot",
                    "message": f"Sorry, an error occurred while generating questions: {e}. Let's try your tech stack again."
                })
                st.session_state.info_stage = "techStack"
            finally:
                st.session_state.pending_operation = None 
                st.session_state.is_loading = False
                st.rerun()
        
        elif op == "process_answer":
            question_text = st.session_state.technical_questions[st.session_state.current_question_index]
            answer_text = st.session_state.current_user_input 
            info['technicalResponses'].append({"question": question_text, "answer": answer_text})
            
            next_idx = st.session_state.current_question_index + 1
            if next_idx < len(st.session_state.technical_questions):
                st.session_state.current_question_index = next_idx
                bot_msg = (f"Thank you for your answer.\n\nNext question:\n"
                           f"{st.session_state.technical_questions[next_idx]}")
                st.session_state.info_stage = "askingQuestion"
            else:
                bot_msg = (f"Thank you. That concludes the technical assessment, {info['fullName']}!\n\n"
                           "Please review your information on the left. If everything is correct, click 'Save and Submit Profile'.")
                st.session_state.info_stage = "completed" 
            st.session_state.chat_history.append({"sender": "bot", "message": bot_msg})
            st.session_state.pending_operation = None 
            st.session_state.is_loading = False
            st.session_state.current_user_input = None 
            st.rerun()

        elif op == "save_profile":
            try:
                if st.session_state.db and st.session_state.user_id:
                    save_success = save_candidate_profile(
                        st.session_state.db, app_id, st.session_state.user_id, info
                    )
                    if save_success:
                        info["saved_to_firestore"] = True
                        st.session_state.chat_history.append({
                            "sender": "bot",
                            "message": "✅ Your profile has been successfully submitted and saved! "
                                       "A recruiter will be in touch if your profile matches our requirements. Thank you! "
                                       "You can ask me general questions about the hiring process or type 'exit' to end the conversation."
                        })
                         # Allow follow-up questions
                        st.session_state.info_stage = "final_confirmation"
                    else: 
                        st.session_state.chat_history.append({
                            "sender": "bot",
                            "message": "❌ Failed to save profile. Please try again or contact support."})
                        st.session_state.info_stage = "completed" 
                else: 
                     st.session_state.chat_history.append({"sender": "bot", "message": "❌ Database not available. Profile not saved."})
                     st.session_state.info_stage = "completed" 
            except Exception as e:
                st.error(f"Save profile error: {e}")
                st.session_state.chat_history.append({"sender": "bot", "message": f"❌ Error saving profile: {e}"})
                st.session_state.info_stage = "completed" 
            finally:
                st.session_state.pending_operation = None
                st.session_state.is_loading = False
                st.rerun()

    if (
        st.session_state.info_stage == "positions_select"
        and st.session_state.position_selected_value
        and not st.session_state.is_loading 
        and not st.session_state.pending_operation 
    ):
        selected_pos = st.session_state.position_selected_value
        info = st.session_state.candidate_info
        info["desiredPositions"] = selected_pos
        st.session_state.chat_history.append({
            "sender": "user", "message": f"I'm interested in: {selected_pos}"
        })
        bot_msg = "Thank you. In which primary tech stack are you proficient? (e.g., Python, React, Java, AWS)"
        st.session_state.info_stage = "techStack"
        st.session_state.chat_history.append({"sender": "bot", "message": bot_msg})
        
        st.session_state.position_selected_value = None 
        st.session_state.current_user_input = None 
        st.session_state.is_loading = False
        st.rerun()

    if (
        st.session_state.current_user_input 
        and not st.session_state.pending_operation 
        and st.session_state.is_loading 
    ):
        processed_input = st.session_state.current_user_input

        # 1. Handle Exit Command
        if processed_input.lower() in ["exit", "quit"]:
            st.session_state.chat_history.append({"sender": "bot", "message": "Exiting conversation. Goodbye!"})
            st.session_state.info_stage = "exit"
            st.session_state.current_user_input = None
            st.session_state.is_loading = False
            st.rerun()
            return 

        # 2. Process Input Based on Current Stage or as Contextual Query
        bot_msg = ""
        next_stage = st.session_state.info_stage 
        info = st.session_state.candidate_info
        current_stage = st.session_state.info_stage
        
        handled_as_stage_specific = False

        if current_stage == "name":
            info["fullName"] = processed_input
            bot_msg = "Great! Now, please enter your official email ID."
            next_stage = "email"
            handled_as_stage_specific = True
        elif current_stage == "email":
            email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if re.match(email_regex, processed_input):
                info["email"] = processed_input
                bot_msg = "Please enter your current location (e.g., City, Country)."
                next_stage = "currentLocation"
                handled_as_stage_specific = True
            else:
                bot_msg = "That doesn't look like a valid email. Please provide a valid email address."
                handled_as_stage_specific = True
        elif current_stage == "currentLocation":
            info["currentLocation"] = processed_input
            bot_msg = "Understood. Now, please enter your contact number."
            next_stage = "phoneNumber" 
            handled_as_stage_specific = True
        elif current_stage == "techStack":
            info["techStack"] = processed_input
            bot_msg = (
                f"Great, {info['fullName']}! Now I'm going to ask you 3 technical questions based on your tech stack ({info['techStack']}). "
                "If you are ready, please say 'OK' or 'yes'."
            )
            next_stage = "awaitingQuestionsConsent"
            handled_as_stage_specific = True
        elif current_stage == "awaitingQuestionsConsent":
            if processed_input.strip().lower() in ["ok", "yes", "ready", "sure"]:
                st.session_state.pending_operation = "generate_questions"
                st.session_state.chat_history.append({"sender": "bot", "message": "Okay, generating technical questions..."})
                st.session_state.current_user_input = None 
                st.session_state.is_loading = True 
                st.rerun()
                return 
            else:
                bot_msg = "Please type 'OK' or 'yes' when you are ready to begin the technical questions."
            handled_as_stage_specific = True 
        elif current_stage == "askingQuestion": 
            st.session_state.pending_operation = "process_answer"
            st.session_state.is_loading = True 
            st.rerun()
            return 
        
        #3. Contextual Fallback for General Queries 
        if not handled_as_stage_specific and not st.session_state.pending_operation :
            try:
                contextual_llm_prompt = (
                    "You are TalentScout, a helpful and professional AI hiring assistant. "
                    "You have just completed a candidate screening or are currently in the process of one. "
                    "The user has sent a message. Refer to the provided conversation history to understand the context. "
                    "Respond helpfully, courteously, and contextually to the user's *last* message in the history. "
                    "If it's a question about the hiring process (general steps, next steps), company (general knowledge about TalentScout or common roles), "
                    "or status of their profile (e.g., 'Is my profile saved?'), answer it appropriately and concisely. "
                    "If the user asks to review their details, you can confirm they are displayed on the left. "
                    "If the question is outside your scope (e.g., specific salary details, internal company policies, direct job placement guarantees) "
                    "or requires specific non-public candidate data beyond what you've collected, politely state that you cannot answer that specific question "
                    "but offer to help with general inquiries related to the hiring process. "
                    "Crucially, do not deviate from your purpose as a hiring assistant. "
                    "If the user types 'exit' or 'quit', guide them to end the conversation."
                )

                bot_msg = call_gemini_api(contextual_llm_prompt, st.session_state.chat_history)
                next_stage = current_stage 
            except Exception as e:
                st.error(f"Error handling contextual query: {e}")
                bot_msg = "I'm sorry, I had a little trouble understanding that. Could you please rephrase or continue with the previous topic?"
        
        #4. Update Chat and State (if no operation was set and no early exit/return)
        if not st.session_state.pending_operation: 
            if bot_msg: 
                st.session_state.chat_history.append({"sender": "bot", "message": bot_msg})
            
            st.session_state.info_stage = next_stage
            st.session_state.current_user_input = None 
            st.session_state.is_loading = False 
            st.rerun()

if __name__ == "__main__":
    main()