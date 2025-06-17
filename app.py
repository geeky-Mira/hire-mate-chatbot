import streamlit as st
import json
import re
import os
st.set_page_config(page_title="HireMate Hiring Assistant", layout="wide")
from llm_service import call_gemini_api 
from firebase_service import initialize_firebase, save_candidate_profile

# New import for the code editor
from streamlit_ace import st_ace 
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
    st.title("🤖 HireMate Hiring Assistant")

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
            {"sender": "bot", "message": "Hello! Welcome to HireMate’s Hiring Assistant. Please note: All data you provide will be used solely for this simulated hiring process and handled with care."}
        )
        st.session_state.chat_history.append(
            {"sender": "bot", "message": "May I have your full name? (You can type 'exit' anytime to end the conversation)"}
        )
    # New state for code editor input
    if "code_input" not in st.session_state:
        st.session_state.code_input = ""

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
        st.subheader("Chat with HireMate AI")
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
        
        # Stage-Specific Input Widgets
        if stage == "askingQuestion" and not st.session_state.is_loading and not st.session_state.pending_operation:
            current_question = st.session_state.technical_questions[st.session_state.current_question_index]
            # Check if it's a coding question
            if "[CODE]" in current_question:
                st.info("This is a coding question. Please use the editor below or upload a file.")
                st.write(current_question.replace("[CODE]", "").strip())

                st.session_state.code_input = st_ace(language="python", theme="tomorrow_night", key="ace_editor", auto_update=True)
                
                uploaded_file = st.file_uploader("Or upload your code file")

                if st.button("Submit Code Answer", key="submit_code_btn"):
                    answer = ""
                    if uploaded_file is not None:
                        answer = uploaded_file.getvalue().decode("utf-8")
                        st.session_state.current_user_input = f"--- CODE FROM FILE ---\n{answer}"
                    else:
                        answer = st.session_state.code_input
                        st.session_state.current_user_input = f"--- CODE FROM EDITOR ---\n{answer}"
                    
                    st.session_state.chat_history.append({"sender": "user", "message": st.session_state.current_user_input})
                    st.session_state.pending_operation = "process_answer"
                    st.session_state.is_loading = True
                    st.rerun()
            # It's a regular theoretical question, so use chat input
            else: 
                pass # The regular chat input will be handled later

        elif stage == "positions_select" and not st.session_state.is_loading and not st.session_state.pending_operation:
            job_options = ["Software Engineer", "Data Scientist", "Product Manager", "UX Designer", "DevOps Engineer", "Cloud Architect", "Cybersecurity Analyst", "Other"]
            st.session_state.position_selected_value = st.selectbox("Please choose your primary desired position from the list:", options=job_options, key="positions_selectbox_widget", index=None, placeholder="Select a position...")
        
        elif stage == "phoneNumber" and not st.session_state.is_loading and not st.session_state.pending_operation:
            st.write("Please enter your phone number:")
            st_phone_number(label="📱 Mobile Number", placeholder="(select country code via dropdown)", default_country="IN", key="phone_number_widget" )
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
                    st.session_state.current_user_input = None; st.session_state.is_loading = False; st.rerun()
                else: st.error("Please enter a valid phone number.")

        elif stage == "experience" and not st.session_state.is_loading and not st.session_state.pending_operation:
            st.write("Enter your years of professional experience (e.g., 0, 1, 5):")
            years = st.number_input(label="Years of Experience", min_value=0, step=1, key="experience_input_widget" )
            if st.button("Confirm Experience", key="confirm_experience_btn"):
                st.session_state.candidate_info["yearsExperience"] = int(years)
                st.session_state.chat_history.append({"sender": "user", "message": str(years)})
                st.session_state.chat_history.append({"sender": "bot", "message": "Which primary job role are you interested in?"})
                st.session_state.info_stage = "positions_select"
                st.session_state.current_user_input = None; st.session_state.is_loading = False; st.rerun()
 
        if st.session_state.is_loading and stage not in ["exit", "final_confirmation", "completed"]:
            with st.spinner("Processing..."): pass 

        chat_input_disabled = (st.session_state.is_loading or st.session_state.pending_operation is not None or stage in ["positions_select", "phoneNumber", "experience", "completed", "exit"])
        
        # Don't show chat input if it's a coding question UI
        is_coding_question = "[CODE]" in st.session_state.technical_questions[st.session_state.current_question_index] if stage == "askingQuestion" and st.session_state.technical_questions else False
        
        if not is_coding_question and stage not in ["positions_select", "phoneNumber", "experience", "completed", "exit"]:
            user_input_from_widget = st.chat_input("Type your message here...", disabled=chat_input_disabled, key="main_chat_input_widget")
            if user_input_from_widget:
                st.session_state.current_user_input = user_input_from_widget.strip()
                st.session_state.chat_history.append({"sender": "user", "message": st.session_state.current_user_input})
                st.session_state.is_loading = True 
                st.rerun() 
        elif chat_input_disabled:
             st.chat_input("Type your message here...", disabled=True, key="main_chat_input_widget_disabled")

        st.markdown("<div style='position: relative; bottom: 0; width: 100%; text-align: left; padding-top: 20px;'><p style='font-size: 0.75rem; color: #9CA3AF;'>&copy; 2024 HireMate. Powered by Gemini & Firebase</p></div>", unsafe_allow_html=True)

    # Handle Pending Operations
    if st.session_state.pending_operation:
        op = st.session_state.pending_operation
        info = st.session_state.candidate_info

        if op == "generate_questions":
            try:
                # UPDATED PROMPT: Includes role, experience, difficulty, and coding question format.
                prompt = (
                    f"You are a technical interviewer for HireMate. Your task is to generate 3 questions for an initial screening. "
                    f"The candidate is applying for the role of '{info['desiredPositions']}' with {info['yearsExperience']} years of experience. "
                    f"Their self-declared tech stack is: \"{info['techStack']}\".\n\n"
                    "INSTRUCTIONS:\n"
                    "1. The questions must be suitable for an initial screening: focus on fundamental concepts, not deep, complex problems.\n"
                    "2. Create a mix of theoretical and practical questions.\n"
                    "3. If you generate a coding question, you MUST prefix it with the tag `[CODE]`.\n"
                    "4. Format the final output as a numbered list (e.g., '1. Question one?', '2. [CODE] Question two?')."
                )
                response_text = call_gemini_api(prompt, []) 
                questions = []
                for line in response_text.split('\n'):
                    match = re.match(r'^\s*\d+\.\s*(.*)$', line.strip())
                    if match: questions.append(match.group(1).strip())

                st.session_state.technical_questions = questions[:3] 
                if st.session_state.technical_questions:
                    bot_msg = f"Okay, let's start with the first question: {st.session_state.technical_questions[0]}"
                    st.session_state.info_stage = "askingQuestion"
                    st.session_state.current_question_index = 0
                else:
                    bot_msg = "I had trouble generating questions. Could you please try re-entering your tech stack with more specific terms?"
                    st.session_state.info_stage = "techStack" 
                st.session_state.chat_history.append({"sender": "bot", "message": bot_msg})
            except Exception as e:
                st.error(f"Question generation error: {e}")
                st.session_state.chat_history.append({"sender": "bot", "message": f"Sorry, an error occurred. Let's try your tech stack again."})
                st.session_state.info_stage = "techStack"
            finally:
                st.session_state.pending_operation = None; st.session_state.is_loading = False; st.rerun()
        
        elif op == "process_answer":
            question_text = st.session_state.technical_questions[st.session_state.current_question_index]
            answer_text = st.session_state.current_user_input 
            info['technicalResponses'].append({"question": question_text, "answer": answer_text})
            
            next_idx = st.session_state.current_question_index + 1
            if next_idx < len(st.session_state.technical_questions):
                st.session_state.current_question_index = next_idx
                bot_msg = f"Thank you. Next question: {st.session_state.technical_questions[next_idx]}"
                st.session_state.info_stage = "askingQuestion"
            else:
                bot_msg = f"Thank you. That concludes the technical assessment, {info['fullName']}! Please review your information and click 'Save and Submit Profile'."
                st.session_state.info_stage = "completed" 
            st.session_state.chat_history.append({"sender": "bot", "message": bot_msg})
            st.session_state.pending_operation = None; st.session_state.is_loading = False; st.session_state.current_user_input = None; st.rerun()

        elif op == "save_profile":
            try:
                if st.session_state.db and st.session_state.user_id:
                    if save_candidate_profile(st.session_state.db, app_id, st.session_state.user_id, info):
                        info["saved_to_firestore"] = True
                        st.session_state.chat_history.append({"sender": "bot", "message": "✅ Profile saved! Now generating personalized feedback based on your answers..."})
                        # NEW: Instead of finishing, trigger feedback generation
                        st.session_state.pending_operation = "generate_feedback"
                    else: 
                        st.session_state.chat_history.append({"sender": "bot", "message": "❌ Failed to save profile. Please try again."})
                        st.session_state.info_stage = "completed"
                        st.session_state.pending_operation = None
                else: 
                     st.session_state.chat_history.append({"sender": "bot", "message": "❌ Database not available. Profile not saved."})
                     st.session_state.info_stage = "completed"
                     st.session_state.pending_operation = None
            except Exception as e:
                st.error(f"Save profile error: {e}")
                st.session_state.chat_history.append({"sender": "bot", "message": f"❌ Error saving profile: {e}"})
                st.session_state.info_stage = "completed"; st.session_state.pending_operation = None
            finally:
                st.session_state.is_loading = False; st.rerun()

        # NEW: Feedback Generation Operation
        elif op == "generate_feedback":
            try:
                responses_str = "\n\n".join([f"Q: {r['question']}\nA: {r['answer']}" for r in info['technicalResponses']])
                feedback_prompt = (
                    "You are a helpful and constructive career coach for HireMate. "
                    f"A candidate named {info['fullName']} has applied for the role of '{info['desiredPositions']}' and completed an initial screening.\n"
                    f"Here are their answers to the technical questions:\n\n{responses_str}\n\n"
                    "Your task is to provide brief, constructive feedback. "
                    "Based on their answers, identify 1-2 key areas where they seem strong and 1-2 potential areas for improvement relevant to the desired job role. "
                    "Keep the tone encouraging and professional. Do not judge, but rather guide. Format the output clearly using Markdown."
                )
                feedback_text = call_gemini_api(feedback_prompt, [])
                bot_msg = "✅ Your profile has been successfully submitted!\n\nHere is some feedback based on your technical answers to help you prepare for future interviews:\n\n" + feedback_text
                bot_msg += "\n\nA recruiter will be in touch if your profile matches our requirements. Thank you! You can now type 'exit' to end."
                st.session_state.chat_history.append({"sender": "bot", "message": bot_msg})
                st.session_state.info_stage = "final_confirmation"
            except Exception as e:
                st.error(f"Feedback generation error: {e}")
                st.session_state.chat_history.append({"sender": "bot", "message": "I had trouble generating feedback, but your profile was saved successfully. Thank you!"})
                st.session_state.info_stage = "final_confirmation"
            finally:
                st.session_state.pending_operation = None; st.session_state.is_loading = False; st.rerun()


    if st.session_state.info_stage == "positions_select" and st.session_state.position_selected_value and not st.session_state.is_loading and not st.session_state.pending_operation:
        selected_pos = st.session_state.position_selected_value
        info = st.session_state.candidate_info; info["desiredPositions"] = selected_pos
        st.session_state.chat_history.append({"sender": "user", "message": f"I'm interested in: {selected_pos}"})
        bot_msg = "Thank you. In which primary tech stack are you proficient? (e.g., Python, React, Java, AWS)"
        st.session_state.info_stage = "techStack"
        st.session_state.chat_history.append({"sender": "bot", "message": bot_msg})
        st.session_state.position_selected_value = None; st.session_state.current_user_input = None; st.session_state.is_loading = False; st.rerun()

    if st.session_state.current_user_input and not st.session_state.pending_operation and st.session_state.is_loading:
        processed_input = st.session_state.current_user_input

        if processed_input.lower() in ["exit", "quit"]:
            st.session_state.chat_history.append({"sender": "bot", "message": "Exiting conversation. Goodbye!"}); st.session_state.info_stage = "exit"
            st.session_state.current_user_input = None; st.session_state.is_loading = False; st.rerun(); return 

        bot_msg = ""; next_stage = st.session_state.info_stage; info = st.session_state.candidate_info; current_stage = st.session_state.info_stage
        handled_as_stage_specific = False

        if current_stage == "name":
            info["fullName"] = processed_input; bot_msg = "Great! Now, please enter your official email ID."; next_stage = "email"; handled_as_stage_specific = True
        elif current_stage == "email":
            if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", processed_input):
                info["email"] = processed_input; bot_msg = "Please enter your current location (e.g., City, Country)."; next_stage = "currentLocation"; handled_as_stage_specific = True
            else: bot_msg = "That doesn't look like a valid email. Please provide a valid email address."; handled_as_stage_specific = True
        elif current_stage == "currentLocation":
            info["currentLocation"] = processed_input; bot_msg = "Understood. Now, please enter your contact number."; next_stage = "phoneNumber" ; handled_as_stage_specific = True
        elif current_stage == "techStack":
            info["techStack"] = processed_input
            bot_msg = f"Great, {info['fullName']}! I'll now generate 3 technical questions based on your profile. If you are ready, please say 'OK' or 'yes'."
            next_stage = "awaitingQuestionsConsent"; handled_as_stage_specific = True
        elif current_stage == "awaitingQuestionsConsent":
            if processed_input.strip().lower() in ["ok", "yes", "ready", "sure"]:
                st.session_state.pending_operation = "generate_questions"
                st.session_state.chat_history.append({"sender": "bot", "message": "Okay, generating technical questions..."})
                st.session_state.current_user_input = None; st.session_state.is_loading = True; st.rerun(); return 
            else: bot_msg = "Please type 'OK' or 'yes' when you are ready."; handled_as_stage_specific = True 
        elif current_stage == "askingQuestion": 
            # This logic now handles theoretical questions from chat input. Coding questions are handled by a button.
            is_coding_q = "[CODE]" in st.session_state.technical_questions[st.session_state.current_question_index] if st.session_state.technical_questions else False
            if not is_coding_q:
                st.session_state.pending_operation = "process_answer"; st.session_state.is_loading = True; st.rerun(); return 
        
        if not handled_as_stage_specific and not st.session_state.pending_operation:
            try:
                contextual_llm_prompt = "You are HireMate, a helpful AI hiring assistant. Respond courteously and contextually to the user's *last* message in the history. If the question is outside your scope, politely state that you cannot answer. Do not deviate from your purpose."
                bot_msg = call_gemini_api(contextual_llm_prompt, st.session_state.chat_history)
                next_stage = current_stage 
            except Exception as e:
                st.error(f"Error handling contextual query: {e}")
                bot_msg = "I'm sorry, I had a little trouble understanding that. Could you please rephrase?"
        
        if not st.session_state.pending_operation: 
            if bot_msg: st.session_state.chat_history.append({"sender": "bot", "message": bot_msg})
            st.session_state.info_stage = next_stage
            st.session_state.current_user_input = None; st.session_state.is_loading = False; st.rerun()

if __name__ == "__main__":
    main()
