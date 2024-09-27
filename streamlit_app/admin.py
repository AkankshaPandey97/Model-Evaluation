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
enriched_table = "enrichedMetadata"  # Table containing questionResult, stepsResult

# Function to load user details from BigQuery UserInfo table
def load_userinfo_data():
    """Load user details from BigQuery UserInfo table."""
    client = bigquery.Client(project=project_id)
    query = f"""
    SELECT firstName, lastName, email, fullName, feedback, password
    FROM `{project_id}.{dataset_id}.UserInfo`
    """
    try:
        query_job = client.query(query)
        df = query_job.result().to_dataframe()  # Convert query result to pandas DataFrame
        return df
    except Exception as e:
        st.error(f"Error fetching user details from BigQuery: {e}")
        return pd.DataFrame()

# Function to load results data from BigQuery
def load_results_data():
    """Load questionResult and stepsResult data from BigQuery."""
    client = bigquery.Client(project=project_id)
    query = f"""
    SELECT 
        questionResult, 
        stepsResult
    FROM `{project_id}.{dataset_id}.{enriched_table}`
    """
    try:
        query_job = client.query(query)
        df = query_job.result().to_dataframe()  # Convert query result to pandas DataFrame
        return df
    except Exception as e:
        st.error(f"Error fetching data from BigQuery: {e}")
        return pd.DataFrame()

# Function to plot the bar chart
def plot_visualization(true_question, true_steps, false_steps):
    labels = ['Questions', 'Steps', 'Null']
    counts = [true_question, true_steps, false_steps]
    colors = ['darkgreen', 'purple', 'orange']

    fig, ax = plt.subplots(figsize=(5, 4))  # Set smaller figure size
    bars = ax.bar(labels, counts, color=colors)

    # Annotate bars with their heights
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + 0.1, f'{int(height)}', ha='center', fontsize=10)

    ax.set_ylim(0, max(counts) + 1)
    ax.set_title("True/False Distribution")
    ax.set_ylabel("Count")
    ax.set_xlabel("Category")
    ax.yaxis.set_major_locator(plt.MultipleLocator(1))  # Y-axis increments by 1

    st.pyplot(fig)

# Admin Page
def admin_page():
    """Admin page that allows the admin to view user details and visualizations."""
    st.title("Admin Dashboard")
    
    # Add sidebar with "Home" button for navigation and logging out
    st.sidebar.header("Navigation")
    if st.sidebar.button("Home"):
        # Clear session state to simulate logout
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Redirect to the login screen
        st.session_state.page = 'login'
        st.experimental_set_query_params(page='login')

    # State for toggling visibility of the user details
    if 'show_user_details' not in st.session_state:
        st.session_state.show_user_details = False

    # Add "USER DETAILS" button to toggle visibility
    if st.button("USER DETAILS"):
        st.session_state.show_user_details = not st.session_state.show_user_details

    # If the button is clicked, show or hide the user details
    if st.session_state.show_user_details:
        df_userinfo = load_userinfo_data()
        if df_userinfo.empty:
            st.warning("No user data available.")
        else:
            st.dataframe(df_userinfo)

    # State for toggling visibility of the graph
    if 'show_visualization' not in st.session_state:
        st.session_state.show_visualization = False

    # Add "Visualisations" button to toggle the graph
    if st.button("Visualisations"):
        st.session_state.show_visualization = not st.session_state.show_visualization

    # If the button is clicked, load and display/hide the graph
    if st.session_state.show_visualization:
        df = load_results_data()

        if df.empty:
            st.warning("No data available to display.")
        else:
            # Count True/False values from questionResult and stepsResult
            true_question_count = df['questionResult'].value_counts().get('True', 0)
            true_steps_count = df['stepsResult'].value_counts().get('True', 0)
            false_steps_count = df['stepsResult'].value_counts().get('False', 0)

            # Plot the graph with the counted values
            plot_visualization(true_question_count, true_steps_count, false_steps_count)

# Run the admin page function
if __name__ == "__main__":
    admin_page()
