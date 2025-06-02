import firebase_admin
from firebase_admin import credentials, firestore, auth
import json
import streamlit as st
import base64

def initialize_firebase(app_id: str, firebase_config_b64_str: str, initial_auth_token: str):
    """
    Initializes Firebase Admin SDK and returns (db_client, auth_module, user_id, error_message).
    - If an existing app is initialized, reuses it.
    - Decodes FIREBASE_CONFIG_B64 → uses Certificate credentials (no ADC fallback).
    - Verifies initial_auth_token (ID token) if provided; otherwise creates/uses a generic backend user.
    """

    # 1) Reuse existing initialized app if present
    if firebase_admin._apps:
        try:
            current_app = firebase_admin.get_app()
            db_client = firestore.client(app=current_app)
            # Admin SDK’s auth module itself
            auth_module = auth    
            user_id = st.session_state.get("user_id", None)
            if user_id:
                return (db_client, auth_module, user_id, None)
        except Exception:
            # If something’s inconsistent, fall through to reinitialize
            pass

    # 2) Decode Base64 service account JSON
    if not firebase_config_b64_str:
        err = "Firebase Service: FIREBASE_CONFIG_B64 is missing."
        return (None, None, None, err)

    try:
        decoded_bytes = base64.b64decode(firebase_config_b64_str)
        service_account_info = json.loads(decoded_bytes.decode("utf-8"))
        cred = credentials.Certificate(service_account_info)
    except (base64.binascii.Error, json.JSONDecodeError, ValueError) as e:
        err = f"Firebase Service: Invalid FIREBASE_CONFIG_B64: {e}"
        return (None, None, None, err)
    except Exception as e:
        err = f"Firebase Service: Error decoding service account: {e}"
        return (None, None, None, err)

    # 3) Initialize Admin SDK
    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db_client = firestore.client()
        auth_module = auth

        user_id = None
        auth_error = None

        # 4) Verify ID token if provided
        if initial_auth_token:
            try:
                decoded_token = auth_module.verify_id_token(initial_auth_token)
                user_id = decoded_token["uid"]
            except Exception as e:
                auth_error = f"Token verification failed: {e}. Creating generic backend user."

        # 5) Create or fetch a “backend‐service” user if no valid user_id
        if not user_id:
            backend_user_email = f"backend-service@{app_id}.app"
            try:
                # Try getting existing user by email
                user_record = auth_module.get_user_by_email(backend_user_email)
                user_id = user_record.uid
            except auth.UserNotFoundError:
                try:
                    # Create a new backend user
                    user_record = auth_module.create_user(
                        email=backend_user_email,
                        display_name="Backend Service"
                    )
                    user_id = user_record.uid
                except Exception as ee:
                    auth_error = (auth_error + f" Failed to create backend user: {ee}"
                                  if auth_error else f"Failed to create backend user: {ee}")
            except Exception as ee:
                auth_error = (auth_error + f" Failed to get backend user: {ee}"
                              if auth_error else f"Failed to get backend user: {ee}")

        if not user_id:
            final_err = f"Could not establish a user identity. Errors: {auth_error}"
            return (db_client, None, None, final_err)

        # 6) Save user_id to session_state for reuse
        st.session_state.user_id = user_id
        return (db_client, auth_module, user_id, None if not auth_error else auth_error)

    except Exception as e:
        err_msg = f"Firebase Service: Full initialization failed: {e}"
        return (None, None, None, err_msg)


def save_candidate_profile(db_client, app_id: str, user_id: str, candidate_data: dict) -> bool:
    """
    Saves candidate_data into Firestore under:
      artifacts/{app_id}/users/{user_id}/candidate_profiles/{autoDocId}

    Returns True if successful, False otherwise.
    """
    if not db_client:
        st.error("Firebase Service: Firestore client not initialized.")
        return False
    if not user_id:
        st.error("Firebase Service: No user ID available. Cannot save data.")
        return False

    # Remove keys with None values to avoid Firestore rejecting null fields
    cleaned_data = {k: v for k, v in candidate_data.items() if v is not None}

    try:
        path = f"artifacts/{app_id}/users/{user_id}/candidate_profiles"
        doc_ref = db_client.collection(path).document()
        doc_ref.set(cleaned_data)
        return True
    except Exception as e:
        st.error(f"Firebase Service: Failed to save profile: {e}")
        return False
