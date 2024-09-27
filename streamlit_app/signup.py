import streamlit as st
import re
from google.cloud import bigquery
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# BigQuery project details
project_id = os.getenv("PROJECT_ID")
dataset_id = os.getenv("DATASET_ID")
table_id = "UserInfo"  # UserInfo table

# Initialize BigQuery Client
client = bigquery.Client(project=project_id)

# Password validation function
def validate_password(password):
    errors = []
    if len(password) < 5 or len(password) > 20:
        errors.append("Password must be between 5 and 20 characters long.")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must include at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        errors.append("Password must include at least one lowercase letter.")
    if not re.search(r'[0-9]', password):
        errors.append("Password must include at least one number.")
    if not re.search(r'[*@!]', password):
        errors.append("Password must include at least one special character (*, @, !).")
    return errors

# Email validation function
def validate_email(email):
    pattern = r"[^@]+@[^@]+\.[^@]+"
    return re.match(pattern, email) is not None

# Name validation function
def validate_name(name):
    return len(name) >= 2 and all(x.isalpha() or x.isspace() for x in name)

# Function to check if email is unique in BigQuery
def is_email_unique(email):
    query = f"""
    SELECT COUNT(*) as count
    FROM `{project_id}.{dataset_id}.{table_id}`
    WHERE email = @email
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", email)]
    )
    query_job = client.query(query, job_config=job_config)
    result = query_job.result()
    for row in result:
        return row['count'] == 0

# Function to save the user data into BigQuery
def save_to_bigquery(first_name, last_name, email, password):
    try:
        full_name = f"{first_name} {last_name}"  # Concatenate first and last name for fullName
        rows_to_insert = [
            {
                "firstName": first_name,
                "lastname": last_name,
                "fullName": full_name,
                "email": email,
                "password": password
            }
        ]

        table_ref = f"{project_id}.{dataset_id}.{table_id}"
        errors = client.insert_rows_json(table_ref, rows_to_insert)
        if errors == []:
            st.success("User successfully registered!")
        else:
            st.error(f"Failed to register user: {errors}")

    except Exception as e:
        st.error(f"An error occurred: {e}")

# Custom CSS for UI styling
def add_custom_css():
    st.markdown("""
    <style>
    .stApp { background-color: #000033; color: white; }
    .stButton button { background-color: #1E90FF; color: white; border-radius: 20px; padding: 12px 24px; font-weight: bold; font-size: 16px; margin-bottom: 10px; border: 2px solid #1C6EA4; transition: background-color 0.3s, transform 0.3s; }
    .stButton button:hover { background-color: #4682B4; transform: scale(1.05); }
    .stTextInput input, .stTextArea textarea { background-color: #F0F8FF; color: #000; border-radius: 12px; font-size: 16px; padding: 12px; }
    .stApp h1 { color: #E0FFFF; font-size: 48px; text-align: center; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.4); }
    .stApp p { font-size: 18px; color: #E0FFFF; }
    </style>
    """, unsafe_allow_html=True)

# Sign up page function
def signup_page():
    add_custom_css()

    st.title("Sign Up")

    # Input fields for first name, last name, email, password
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    email = st.text_input("Email")

    show_password = st.checkbox("Show password")
    password = st.text_input("Password", type="text" if show_password else "password")
    confirm_password = st.text_input("Confirm Password", type="text" if show_password else "password")

    if st.button("Sign Up"):
        # Validate the inputs
        errors = validate_password(password)
        name_error = not validate_name(first_name) or not validate_name(last_name)
        
        # Show validation errors for names
        if not validate_name(first_name):
            st.error("First name must contain at least 2 characters and only letters.")
        if not validate_name(last_name):
            st.error("Last name must contain at least 2 characters and only letters.")
        
        # Check if passwords match
        if password != confirm_password:
            st.error("Passwords do not match.")
        # Validate email format
        elif not validate_email(email):
            st.error("Please enter a valid email address.")
        # Ensure email is unique
        elif not is_email_unique(email):
            st.error("This email is already registered. Please use a different email.")
        # Show password validation errors
        elif errors:
            st.error("Please fix the following errors:")
            for error in errors:
                st.write(f"- {error}")
        # If all validations pass, save to BigQuery
        elif not name_error and password == confirm_password:
            save_to_bigquery(first_name, last_name, email, password)
            st.success("Sign up successful! You can now log in.")
            st.markdown("[Go to Login Page](?page=login)")

# Call the signup page function
signup_page()
