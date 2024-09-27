import streamlit as st
import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv
import os
from openai_utils import get_openai_answer  # Import OpenAI utilities

# Load environment variables
load_dotenv()

# BigQuery project details
project_id = os.getenv("PROJECT_ID")
dataset_id = os.getenv("DATASET_ID")
table_id = os.getenv("TABLE_ID")  # This is your table containing metadata
enriched_table = "enrichedMetadata"  # Table to store the StepsGeneratedAnswer and stepsResult

# Function to load test case steps and answers from BigQuery, including the "Steps" column from Annotator Metadata
@st.cache_data
def load_steps_data_from_bigquery():
    """Load test case steps and answers from BigQuery."""
    client = bigquery.Client(project=project_id)
    query = f"""
    SELECT 
        Question, 
        task_id,
        `Annotator Metadata`.Steps AS Steps, 
        `Final answer` AS correct_answer,
        extractedData
    FROM `{project_id}.{dataset_id}.{table_id}`
    """
    try:
        query_job = client.query(query)
        df = query_job.result().to_dataframe()  # Convert query result to pandas DataFrame
        return df
    except Exception as e:
        st.error(f"Error fetching data from BigQuery: {e}")
        return pd.DataFrame()

# Function to update the StepsGeneratedAnswer, sessionId, and stepsResult in enrichedMetadata table
def update_steps_result_in_enriched_metadata(task_id: str, steps_generated_answer: str, session_id: str, steps_result: str):
    """Update the StepsGeneratedAnswer, sessionId, and stepsResult columns in the enrichedMetadata table in BigQuery."""
    client = bigquery.Client(project=project_id)
    query = f"""
    UPDATE `{project_id}.{dataset_id}.{enriched_table}`
    SET StepsGeneratedAnswer = @steps_generated_answer, 
        sessionId = @session_id, 
        stepsResult = @steps_result
    WHERE task_id = @task_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("steps_generated_answer", "STRING", steps_generated_answer),
            bigquery.ScalarQueryParameter("session_id", "STRING", session_id),
            bigquery.ScalarQueryParameter("steps_result", "STRING", steps_result),
            bigquery.ScalarQueryParameter("task_id", "STRING", task_id)
        ]
    )
    try:
        query_job = client.query(query, job_config=job_config)
        query_job.result()  # Wait for the query to complete

    except Exception as e:
        st.error(f"Failed to update StepsGeneratedAnswer, sessionId, and stepsResult in BigQuery: {e}")

def remove_final_answer_from_steps(steps, final_answer):
    """
    Remove the final answer from the steps if it exists as a substring.
    Args:
    - steps: List of steps as strings.
    - final_answer: The final answer string to be removed.

    Returns:
    - List of steps with the final answer removed from each step.
    """
    if not final_answer:
        return steps  # If no final answer is given, return steps as is
    
    cleaned_steps = []
    for step in steps:
        # Remove the final answer substring if it exists in the step
        cleaned_step = step.replace(final_answer, "").strip()
        cleaned_steps.append(cleaned_step)
    return cleaned_steps

def validation_page():
    # Add a Back button at the top to navigate to the testing page
    if st.button("Back to Test Cases"):
        # Navigate back to the testing page
        st.session_state.page = 'testing'
        st.experimental_set_query_params(page='testing')
        
    # Display the title below the Skip button
    st.title("Test Case Validation")

    # Load the steps dynamically from BigQuery
    df_steps = load_steps_data_from_bigquery()

    # If there's an issue loading the data, exit
    if df_steps.empty:
        return

    # Display the previously selected test case (from session state)
    selected_test_case = st.session_state.get('selected_test_case', 'No test case selected')
    st.markdown(f"<h5 style='color: yellow;'>Your Test Case: {selected_test_case}</h5>", unsafe_allow_html=True)

    # Check if the 'selected_test_case' is in the loaded dataframe
    if selected_test_case != 'No test case selected' and 'Question' in df_steps.columns:
        # Filter steps for the selected test case
        case_data = df_steps[df_steps['Question'] == selected_test_case]
        steps = case_data['Steps'].tolist()  # Extract the steps from the "Annotator Metadata"
        final_answer = case_data['correct_answer'].values[0]  # Get the final answer for the selected test case
        task_id = case_data['task_id'].values[0]  # Get task_id to use for updates
        extracted_data = case_data['extractedData'].values[0]  # Extract the 'extractedData' for the selected test case

        # Remove the final answer from the steps if it is a substring
        cleaned_steps = remove_final_answer_from_steps(steps, final_answer)

        steps = cleaned_steps  # Use the cleaned steps for display
        steps.insert(0, "Select a step")  # Add the default "Select a step" option
    else:
        steps = ["Select a step"]
        task_id = None
        final_answer = None
        extracted_data = ""  # No extracted data by default

    # Ensure session state for selected_step and step_text
    if 'selected_step' not in st.session_state:
        st.session_state.selected_step = "Select a step"
        st.session_state.step_text = ""
        st.session_state.validation_complete = False  # Track whether validation is done

    # Dropdown for selecting steps dynamically
    selected_step = st.selectbox(
        "Choose a step:",
        steps,
        index=steps.index(st.session_state.selected_step) if st.session_state.selected_step in steps else 0
    )

    # Update session state when user selects a step
    st.session_state.selected_step = selected_step

    # If a valid step is selected (not the default option), display it in a text area for editing
    if selected_step != "Select a step":
        st.session_state.step_text = selected_step  # Set the original step as default in the text area

    # Text area for the user to edit the steps
    edited_step = st.text_area("Edit Step:", value=st.session_state.step_text, height=100)
    
    # Update the step_text in session state as the user edits it
    st.session_state.step_text = edited_step

    # **Answer Button**: Send the test case, edited steps, and extracted data to the LLM
    if st.button('Answer'):
        if st.session_state.selected_step == "Select a step":
            st.warning("Please select a step before generating an answer.")
        else:
            # Use the edited step text and include extracted data in the context
            context = f"Test Case: {selected_test_case}\nSteps: {st.session_state.step_text}\n"
            if extracted_data:
                context += f"Extracted Data: {extracted_data}\n"
            
            answer = get_openai_answer(selected_test_case, context)
            
            # Store the answer in session state for later use in validation
            st.session_state.answer = answer

            # Display the generated answer
            st.text_area("Generated Answer:", value=answer, height=100)

            # Store the generated answer in the enrichedMetadata table along with the session ID
            session_id = st.session_state.get('session_id', 'default_session')  # Get session_id from session state
            if task_id:
                update_steps_result_in_enriched_metadata(task_id, st.session_state.answer, session_id, None)

    # **Validate Button**: Compare if the final answer is a substring of the generated answer
    if st.button("Validate"):
        # Retrieve the correct answer from the case data
        correct_answer = final_answer if final_answer else None

        # Ensure an answer exists in the session state before validating
        if 'answer' not in st.session_state:
            st.warning("Please generate an answer before validating.")
        else:
            # Retrieve the generated answer from session state
            generated_answer = st.session_state.answer

            # Compare the generated answer with the correct answer and set validation result
            if correct_answer and correct_answer.strip().lower() in generated_answer.strip().lower():
                st.success("The answer is correct! The final answer is a substring of the generated answer.")
                validation_result = "True"
            else:
                st.error("The answer is wrong! The final answer is not in the generated answer.")
                validation_result = "False"
           
            # Update the validation result in the enrichedMetadata table
            if task_id:
                update_steps_result_in_enriched_metadata(task_id, st.session_state.answer, st.session_state.session_id, validation_result)

    # **Next Button**: Always show the Next button, regardless of the validation result
    if st.button("Next"):
        # Navigate to the visualization page
        st.session_state.page = 'visualization'
        st.experimental_set_query_params(page='visualization')
