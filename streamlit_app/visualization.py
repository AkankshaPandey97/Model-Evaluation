import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from google.cloud import bigquery
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# BigQuery project details
project_id = os.getenv("PROJECT_ID")
dataset_id = os.getenv("DATASET_ID")
enriched_table = "enrichedMetadata"  # Table containing questionResult, stepsResult, and sessionId

# Function to load questionResult and stepsResult data from enrichedMetadata for the current session
@st.cache_data(ttl=60)
def load_result_data(session_id, result_column):
    """Load result data (questionResult or stepsResult) for the ongoing session from enrichedMetadata."""
    client = bigquery.Client(project=project_id)
    query = f"""
    SELECT 
        {result_column}, task_id
    FROM `{project_id}.{dataset_id}.{enriched_table}`
    WHERE sessionId = @session_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("session_id", "STRING", session_id)
        ]
    )
    try:
        query_job = client.query(query, job_config=job_config)
        df = query_job.result().to_dataframe()  # Convert query result to pandas DataFrame
        return df
    except Exception as e:
        st.error(f"Error fetching data from BigQuery: {e}")
        return pd.DataFrame()

# Function to plot and display a bar chart with enhanced annotations
def plot_bar_chart(labels, counts, title, colors):
    fig, ax = plt.subplots(figsize=(3, 2))  # Adjusted figure size

    # Plot the bar chart
    bars = ax.bar(labels, counts, color=colors)

    # Add annotations to show the exact counts on top of the bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + 0.05, f'{count}', ha='center', fontsize=14, color='black')

    # Set chart title and axis labels
    ax.set_title(title, fontsize=11)
    ax.set_xlabel('Validation Result', fontsize=8)
    ax.set_ylabel('Count', fontsize=8)

    # Set the Y-axis to start from 0, with increments by 1
    ax.set_ylim(0, max(counts) + 1)
    ax.yaxis.set_major_locator(plt.MultipleLocator(1))

    return fig

# Function to save feedback to BigQuery UserInfo table
def save_feedback_to_bigquery(email, feedback):
    """Save feedback to the BigQuery UserInfo table for the logged-in user using MERGE."""
    client = bigquery.Client(project=project_id)
    query = f"""
    MERGE `{project_id}.{dataset_id}.UserInfo` T
    USING (
        SELECT @user_email AS email, @feedback AS feedback
    ) S
    ON T.email = S.email
    WHEN MATCHED THEN
      UPDATE SET feedback = S.feedback
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("feedback", "STRING", feedback),
            bigquery.ScalarQueryParameter("user_email", "STRING", email)
        ]
    )
    try:
        query_job = client.query(query, job_config=job_config)
        query_job.result()  # Wait for the query to finish
        st.sidebar.success("Feedback saved successfully!")
    except Exception as e:
        st.error(f"Error saving feedback to BigQuery: {e}")


# Feedback functionality
def feedback_section():
    """Render the feedback section in the sidebar and handle saving feedback."""
    # Ensure the user is logged in before showing feedback section
    if 'session_id' not in st.session_state or 'user_email' not in st.session_state:
        st.sidebar.warning("Please log in to provide feedback.")
        return

    # State for toggling visibility of the feedback text box
    if 'show_feedback' not in st.session_state:
        st.session_state.show_feedback = False

    # Button to toggle visibility of feedback box
    if st.sidebar.button("Give Feedback"):
        st.session_state.show_feedback = not st.session_state.show_feedback

    # If the button is clicked, show or hide the feedback text box
    if st.session_state.show_feedback:
        feedback = st.sidebar.text_area("Your Feedback", key="feedback_text")

        # Save feedback button
        if st.sidebar.button("Save Feedback"):
            user_email = st.session_state.get('user_email', '')  # Get the user's email from session state
            if feedback and user_email:
                save_feedback_to_bigquery(user_email, feedback)
                st.sidebar.success("Feedback saved successfully!")
            else:
                st.sidebar.warning("Please write feedback and ensure the user is logged in.")

# Visualization Page
def visualization_page():
    
    # Call the feedback section to display feedback options in the sidebar
    feedback_section()

    # Add a "Back" button at the top to go to the validation page
    if st.button("Back to Validation Page"):
        st.session_state.page = 'validation'
        st.experimental_set_query_params(page='validation')

    st.title("Validation Results")

    # Ensure that the session ID is available in the session state
    session_id = st.session_state.get('session_id', None)

    if not session_id:
        st.warning("Session ID not found. Please ensure you're logged in.")
        return

    # State for toggling visibility of graphs
    if 'show_question_graph' not in st.session_state:
        st.session_state.show_question_graph = False

    if 'show_steps_graph' not in st.session_state:
        st.session_state.show_steps_graph = False

    if 'show_overall_graph' not in st.session_state:
        st.session_state.show_overall_graph = False

    # State for toggling visibility of the overview table
    if 'show_overview_table' not in st.session_state:
        st.session_state.show_overview_table = False

    # Button to toggle visibility of the "Overview" table
    if st.button("Overview"):
        st.session_state.show_overview_table = not st.session_state.show_overview_table

    # If the button is clicked, show or hide the table
    if st.session_state.show_overview_table:
        # Load questionResult and stepsResult data from BigQuery for the current session
        df_question = load_result_data(session_id, "questionResult")
        df_steps = load_result_data(session_id, "stepsResult")

        if df_question.empty or df_steps.empty:
            st.warning("No data available for the ongoing session.")
        else:
            # Merge both dataframes on task_id
            merged_df = pd.merge(df_question, df_steps, on='task_id', how='outer')

        # Add Test Case and Steps Outcome columns
        merged_df['Test Case Outcome'] = merged_df['questionResult'].apply(lambda x: '✅' if x == 'True' else '❌')

        # Adjust Steps Outcome based on Test Case Outcome
        def compute_steps_outcome(row):
            if row['Test Case Outcome'] == '✅':
                return '-'
            else:
                return '✅' if row['stepsResult'] == 'True' else '❌'

        # Populate Steps Outcome based on the logic above
        merged_df['Steps Outcome'] = merged_df.apply(compute_steps_outcome, axis=1)

        # Display the table with the task_id, Test Case Outcome, and Steps Outcome
        st.table(merged_df[['task_id', 'Test Case Outcome', 'Steps Outcome']])

    # Button to toggle visibility of "Outcome from Question" graph
    if st.button("Outcome from Question"):
        st.session_state.show_question_graph = not st.session_state.show_question_graph

    # If the button is clicked, show or hide the graph for questionResult
    if st.session_state.show_question_graph:
        # Load questionResult data from BigQuery for the current session
        df_question = load_result_data(session_id, "questionResult")

        # If no data is available, show a message
        if df_question.empty:
            st.warning("No data available for the ongoing session.")
        else:
            # Count True and False values from the questionResult column
            question_result_counts = df_question['questionResult'].value_counts().reindex(["True", "False"], fill_value=0)

            true_count = question_result_counts['True']
            false_count = question_result_counts['False']

            st.subheader(f"Total True: {true_count}")
            st.subheader(f"Total False: {false_count}")

            # Plot the True/False validation result counts
            fig = plot_bar_chart(['True', 'False'], [true_count, false_count], 'Validation Results: True vs False', ['purple', 'orange'])
            st.pyplot(fig)

    # Button to toggle visibility of "Outcome from Steps" graph
    if st.button("Outcome from Steps"):
        st.session_state.show_steps_graph = not st.session_state.show_steps_graph

    # If the button is clicked, show or hide the graph for stepsResult
    if st.session_state.show_steps_graph:
        # Load stepsResult data from BigQuery for the current session
        df_steps = load_result_data(session_id, "stepsResult")

        # If no data is available, show a message
        if df_steps.empty:
            st.warning("No data available for the ongoing session.")
        else:
            # Count True, False, and Skipped values from the stepsResult column
            steps_result_counts = df_steps['stepsResult'].value_counts().reindex(["True", "False", "Skipped"], fill_value=0)

            true_count = steps_result_counts['True']
            false_count = steps_result_counts['False']
            skipped_count = steps_result_counts['Skipped']

            st.subheader(f"Total True: {true_count}")
            st.subheader(f"Total False: {false_count}")
            st.subheader(f"Total Skipped: {skipped_count}")

            # Plot the True/False/Skipped validation result counts
            fig = plot_bar_chart(['True', 'False', 'Skipped'], [true_count, false_count, skipped_count], 'Steps Results: True vs False vs Skipped', ['green', 'red', 'blue'])
            st.pyplot(fig)

    # Button to toggle visibility of the new "Overall Outcome" graph
    if st.button("Overall Outcome"):
        st.session_state.show_overall_graph = not st.session_state.show_overall_graph

    # If the button is clicked, show or hide the overall graph
    if st.session_state.show_overall_graph:
        # Load questionResult data from BigQuery for the current session
        df_question = load_result_data(session_id, "questionResult")

        # Load stepsResult data from BigQuery for the current session
        df_steps = load_result_data(session_id, "stepsResult")

        # Ensure both dataframes have data
        if df_question.empty or df_steps.empty:
            st.warning("No data available for the ongoing session.")
        else:
            # Count True values from questionResult
            question_true_count = df_question['questionResult'].value_counts().get('True', 0)

            # Count True and False values from stepsResult
            steps_true_count = df_steps['stepsResult'].value_counts().get('True', 0)
            steps_false_count = df_steps['stepsResult'].value_counts().get('False', 0)

            # Plot the graph with three bars
            labels = ['Questions', 'Steps', 'Null']
            counts = [question_true_count, steps_true_count, steps_false_count]
            colors = ['purple', 'green', 'red']

            st.subheader(f"Question: {question_true_count}")
            st.subheader(f"Steps: {steps_true_count}")
            st.subheader(f"Null: {steps_false_count}")

            # Plot the overall outcome graph
            fig = plot_bar_chart(labels, counts, 'Overall Outcome: True and False', colors)
            st.pyplot(fig)

# Main function to run the page
if __name__ == "__main__":
    visualization_page()
