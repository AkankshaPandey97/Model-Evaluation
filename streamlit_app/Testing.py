import streamlit as st
import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv
import os
from openai_utils import get_openai_answer, update_testcase_answer_in_bigquery  # Import utilities

# Load environment variables
load_dotenv()

# Ensure OpenAI API Key is set
openai_key = os.getenv('OPENAI_API_KEY')
if not openai_key:
    st.error("OpenAI API key not found. Make sure it's set in the .env file.")

# BigQuery project details
project_id = os.getenv("PROJECT_ID")
dataset_id = os.getenv("DATASET_ID")
table_id = os.getenv("TABLE_ID")  # Table for test cases and extracted data
enriched_table = "enrichedMetadata"  # Table for storing results

# Function to load test case data along with extracted data from BigQuery
@st.cache_data
def load_test_case_data():
    """Load test case data along with extracted data from BigQuery."""
    client = bigquery.Client(project=project_id)
    query = f"""
    SELECT Question, task_id, `Final answer`, extractedData FROM `{project_id}.{dataset_id}.{table_id}`
    """
    try:
        query_job = client.query(query)
        df = query_job.result().to_dataframe()  # Convert query result to pandas DataFrame
        return df
    except Exception as e:
        st.error(f"Error fetching data from BigQuery: {e}")
        return pd.DataFrame()

# Function to update the generated answer, sessionId, questionResult, and stepsResult in enrichedMetadata table
def update_metadata(task_id: str, generated_answer: str, session_id: str, question_result: str, steps_result: str):
    """Update the GeneratedAnswer, sessionId, questionResult, and stepsResult columns in the enrichedMetadata table."""
    client = bigquery.Client(project=project_id)
    query = f"""
    UPDATE `{project_id}.{dataset_id}.{enriched_table}`
    SET GeneratedAnswer = @generated_answer, 
        sessionId = @session_id, 
        questionResult = @question_result,
        stepsResult = @steps_result
    WHERE task_id = @task_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("generated_answer", "STRING", generated_answer),
            bigquery.ScalarQueryParameter("session_id", "STRING", session_id),
            bigquery.ScalarQueryParameter("question_result", "STRING", question_result),
            bigquery.ScalarQueryParameter("steps_result", "STRING", steps_result),
            bigquery.ScalarQueryParameter("task_id", "STRING", task_id)
        ]
    )
    try:
        query_job = client.query(query, job_config=job_config)
        query_job.result()  # Wait for the query to complete

    except Exception as e:
        st.error(f"Failed to update enrichedMetadata table in BigQuery: {e}")

# Add custom CSS for styling
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
        .highlight-box {
            background-color: #FFFF99;
            border: 2px solid #FFD700;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-weight: bold;
            color: #000;
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

def testing_page():
    add_custom_css()

    # Sidebar GUIDE section
    with st.sidebar:
        with st.expander("ℹ️ GUIDE"):
            st.markdown(
                """
                1. **Select a Test Case**: 
                   - Choose a test case from the dropdown menu.
                2. **Click 'Answer'**:
                   - Generate an answer using the LLM for that test case.
                3. **Validate Your Answer**:
                   - Check if the generated answer is correct.
                4. **Proceed**:
                   - If validated, click 'NEXT' to move to the next test case.
                """, 
                unsafe_allow_html=True
            )

    # Main page content
    st.title("Test Case Validator")

    # Load the test case data from BigQuery
    df = load_test_case_data()

    if df.empty:
        return

    required_columns = ['Question', 'task_id', 'Final answer', 'extractedData']
    if not all(col in df.columns for col in required_columns):
        st.error(f"Missing columns: {', '.join(required_columns)}")
        return

    # Dropdown for test cases
    test_cases = ["Select a test case"] + df['Question'].tolist()

    if 'selected_test_case' not in st.session_state:
        st.session_state.selected_test_case = "Select a test case"
    if 'answer' not in st.session_state:
        st.session_state.answer = ""
    if 'final_answer' not in st.session_state:
        st.session_state.final_answer = ""
    if 'task_id' not in st.session_state:
        st.session_state.task_id = ""
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = ""

    # Ensure session_id is available
    if 'session_id' not in st.session_state:
        st.session_state.session_id = "session_id_missing"  # Default

    # Display dropdown for selecting test case
    selected_test_case = st.selectbox(
        "Choose a test case:",
        test_cases,
        index=test_cases.index(st.session_state.selected_test_case)
    )

    st.session_state.selected_test_case = selected_test_case

    # Fetch the task_id, final answer, and extracted data for the selected test case
    if selected_test_case != "Select a test case":
        st.session_state.task_id = df.loc[df['Question'] == selected_test_case, 'task_id'].values[0]
        st.session_state.final_answer = df.loc[df['Question'] == selected_test_case, 'Final answer'].values[0]
        st.session_state.extracted_data = df.loc[df['Question'] == selected_test_case, 'extractedData'].values[0]

    # Display the generated answer if it exists
    if 'answer' in st.session_state and st.session_state.answer:
        st.text_area("Generated Answer:", value=st.session_state.answer, height=100)

    # Generate answer using OpenAI API
    if st.button('Answer') and selected_test_case != "Select a test case":
        context = f"Question: {selected_test_case}\n"
        if st.session_state.extracted_data:
            context += f"Extracted Data: {st.session_state.extracted_data}\n"
        
        st.session_state.answer = get_openai_answer(selected_test_case, context)
        
        # Display the generated answer
        st.text_area("Generated Answer:", value=st.session_state.answer, height=100)

        # Store generated answer, sessionId, and validation result in the enrichedMetadata table
        update_metadata(
            st.session_state.task_id, 
            st.session_state.answer, 
            st.session_state.session_id,
            "Pending",  # Default questionResult
            "Pending"  # Default stepsResult
        )

    # Display the expected answer
    st.markdown("**Expected Answer:**")
    st.markdown(f"<div class='highlight-box'>{st.session_state.final_answer}</div>", unsafe_allow_html=True)

    # Validate the generated answer
    if st.button("Validate"):
        if selected_test_case == "Select a test case":
            st.warning("Please select a test case before validating.")
        elif not st.session_state.answer:
            st.warning("Please click 'Answer' to generate an answer before validating.")
        else:
            generated_answer = st.session_state.answer.strip().lower()
            final_answer = st.session_state.final_answer.strip().lower()

            # Set the initial validation results
            question_result = "False"
            steps_result = "Pending"

            # Validate if the generated answer contains the final answer
            if final_answer in generated_answer:
                st.success("The answer is correct!")
                question_result = "True"
                steps_result = "Skipped"  # If the answer is correct, set stepsResult to 'Skipped'
            else:
                st.error("The answer is wrong!")

            # Update the validation results in the enrichedMetadata table
            update_metadata(
                st.session_state.task_id,
                st.session_state.answer,
                st.session_state.session_id,
                question_result,
                steps_result
            )

    # Next button
    if st.button("NEXT"):
        if selected_test_case == "Select a test case":
            st.warning("Please select a test case before proceeding.")
        else:
            st.session_state.page = 'validation'
            st.experimental_set_query_params(page='validation')
