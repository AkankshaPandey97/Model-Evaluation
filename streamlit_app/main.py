import streamlit as st
import pandas as pd
from Testing import testing_page
from validation import validation_page
from visualization import visualization_page
from admin import admin_page
from openai_utils import get_question_from_bigquery, get_openai_answer
from dotenv import load_dotenv
import os
import uuid
from google.cloud import bigquery

# Load environment variables from .env file
load_dotenv()

# Ensure that the credentials environment variable is set
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not credentials_path:
    raise EnvironmentError("GOOGLE_APPLICATION_CREDENTIALS is not set. Please set it in the .env file or system environment.")

# BigQuery project details
project_id = os.getenv("PROJECT_ID")
dataset_id = os.getenv("DATASET_ID")
userinfo_table = "UserInfo"  # Your BigQuery table

# Hardcoded admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123*"

# Load custom CSS
def add_custom_css():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #000033;
            color: white;
        }
        .stButton button {
            background-color: #1E90FF;
            color: white;
            border-radius: 20px;
            padding: 12px 24px;
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 10px;
            border: 2px solid #1C6EA4;
            transition: background-color 0.3s, transform 0.3s;
        }
        .stButton button:hover {
            background-color: #4682B4;
            transform: scale(1.05);
        }
        .stTextInput input, .stTextArea textarea {
            background-color: #F0F8FF;
            color: #000;
            border-radius: 12px;
            font-size: 16px;
            padding: 12px;
        }
        h1, h2, h3, h4, h5, h6, p {
            font-family: 'Arial', sans-serif;
        }
        .stApp h1 {
            color: #E0FFFF;
            font-size: 48px;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.4);
        }
        .stApp p {
            font-size: 18px;
            color: #E0FFFF;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Function to fetch user login data from BigQuery
def load_user_data_from_bigquery():
    """Load user data from the UserInfo table in BigQuery."""
    client = bigquery.Client(project=project_id)
    query = f"""
    SELECT email, password FROM `{project_id}.{dataset_id}.{userinfo_table}`
    """
    try:
        query_job = client.query(query)
        df = query_job.result().to_dataframe()
        return df
    except Exception as e:
        st.error(f"Error fetching data from BigQuery: {e}")
        return pd.DataFrame(columns=["email", "password"])

# Validate user credentials from BigQuery
def validate_user(email, password):
    """Validate user login credentials using the UserInfo table in BigQuery."""
    df = load_user_data_from_bigquery()

    # Check if 'email' and 'password' columns exist
    if 'email' not in df.columns or 'password' not in df.columns:
        st.error("The UserInfo table does not have 'email' and 'password' columns.")
        return False

    # Validate the user
    user = df[(df["email"] == email) & (df["password"] == password)]
    return not user.empty

# Admin login functionality
def admin_login():
    st.markdown("### Admin Access")
    
    if 'show_admin_login' not in st.session_state:
        st.session_state.show_admin_login = False

    if st.button("Admin Login"):
        st.session_state.show_admin_login = not st.session_state.show_admin_login

    if st.session_state.show_admin_login:
        admin_username = st.text_input("Admin Username", key="admin_username")
        admin_password = st.text_input("Admin Password", type="password", key="admin_password")
        
        if st.button("Login", key="admin_login"):
            if admin_username == ADMIN_USERNAME and admin_password == ADMIN_PASSWORD:
                st.success("Admin logged in successfully!")
                st.session_state.page = 'admin_dashboard'
                st.experimental_set_query_params(page='admin_dashboard')
            else:
                st.error("Invalid credentials. Please try again.")

# Helper function to navigate between pages
def navigate_to(page):
    st.session_state.page = page
    st.experimental_set_query_params(page=page)

# Function to generate and store a session_id after login/signup
def generate_session_id():
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = str(uuid.uuid4())  # Generate a unique session_id
    return st.session_state['session_id']

# Main page with user login, admin access, and page navigation
def main_page():
    add_custom_css()  # Apply custom CSS

    # Initialize session state for page navigation if not already set
    if 'page' not in st.session_state:
        st.session_state.page = 'login'

    # Sidebar Admin Login
    with st.sidebar:
        admin_login()

    # Page Navigation Logic
    if st.session_state.page == 'login':
        st.title("Welcome to Our Application!")

        # User Login Section
        st.header("User Login")
        email = st.text_input("Email", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        if st.button("Login"):
            if validate_user(email, password):  # Now using BigQuery for validation
                st.success(f"Welcome back, {email}!")
                
                # Set user email in the session state
                st.session_state['user_email'] = email

                # Generate a session_id after login
                session_id = generate_session_id()
                st.write(f"Session ID: {session_id}")  # Display session_id for debugging (can be removed later)
                navigate_to('testing')
            else:
                st.error("Invalid email or password. Please try again.")

        # Button to navigate to the sign-up page
        if st.button("Sign Up as a New User"):
            navigate_to('signup')

    elif st.session_state.page == 'signup':
        from signup import signup_page
        signup_page()  # Call the signup page logic

    elif st.session_state.page == 'testing':
        testing_page()  # Call the function from Testing.py

    elif st.session_state.page == 'validation':
        validation_page()  # Call the function from validation.py

    elif st.session_state.page == 'visualization':
        visualization_page()  # Call the function from visualization.py

    elif st.session_state.page == 'admin_dashboard':
        admin_page()  # Call the function from admin.py

# Main Entry Point
if __name__ == "__main__":
    main_page()
