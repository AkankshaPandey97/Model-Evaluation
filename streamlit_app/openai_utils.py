import openai
import tiktoken
import os
from google.cloud import bigquery
from collections import OrderedDict
from dotenv import load_dotenv
from google.cloud import storage

# Load .env file if present
load_dotenv()

# Set up OpenAI API Key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

if openai.api_key is None:
    raise EnvironmentError("OpenAI API key is not set in the environment.")

# Cache setup (FIFO)
class FIFOCache:
    def __init__(self, capacity=10):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        return self.cache.get(key, None)

    def put(self, key, value):
        if len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)  # FIFO removal
        self.cache[key] = value

cache = FIFOCache()

# Token management using cl100k_base for GPT-4 and GPT-3.5-turbo
def get_token_count(text, model="gpt-4"):
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)
        return len(tokens), tokens
    except Exception as e:
        raise RuntimeError(f"Error while counting tokens: {e}")

# Define your project details
project_id = os.getenv("PROJECT_ID")
dataset_id = os.getenv("DATASET_ID")
table_id = os.getenv("TABLE_ID")

# GCP BigQuery Data Retrieval
def get_question_from_bigquery():
    client = bigquery.Client(project=project_id)
    query = f"""
    SELECT 
        COALESCE(extractedData, Question) AS question, 
        task_id 
    FROM `{project_id}.{dataset_id}.{table_id}`
    LIMIT 1
    """
    try:
        query_job = client.query(query)
        results = query_job.result()
        for row in results:
            return row["question"], row["task_id"]
    except Exception as e:
        raise RuntimeError(f"Error retrieving question from BigQuery: {e}")

def get_annotator_metadata_from_bigquery(task_id):
    client = bigquery.Client(project=project_id)
    query = f"""
    SELECT Annotator_Metadata, Number_of_tools, Tools, How_long_did_this_take,
           Number_of_steps, Steps, Final_answer, gcs_file_path
    FROM `{project_id}.{dataset_id}.{table_id}`
    WHERE task_id = @task_id
    LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("task_id", "STRING", task_id)
        ]
    )
    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        for row in results:
            return {
                "annotator_metadata": row['Annotator_Metadata'],
                "number_of_tools": row['Number_of_tools'],
                "tools": row['Tools'],
                "time_taken": row['How_long_did_this_take'],
                "number_of_steps": row['Number_of_steps'],
                "steps": row['Steps'],
                "final_answer": row['Final_answer'],
                "gcs_file_path": row['gcs_file_path']
            }
    except Exception as e:
        raise RuntimeError(f"Error retrieving metadata from BigQuery: {e}")

# Function to read file content from Google Cloud Storage
def read_gcs_file(gcs_file_path):
    try:
        client = storage.Client()
        bucket_name, file_name = gcs_file_path.split("/", 1)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        return blob.download_as_text()
    except Exception as e:
        raise RuntimeError(f"Error reading file from GCS: {e}")

# OpenAI API call with chat-based model
def get_openai_answer(question: str, context: str, gcs_file_path: str = None,
                      temperature: float = 0.2, max_tokens: int = 150, top_p: float = 0.3) -> str:
    if gcs_file_path:
        # Check file type and read accordingly
        if gcs_file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return "Image files are not supported for text processing."
        else:
            gcs_content = read_gcs_file(gcs_file_path)
            context = f"{gcs_content}\n{context}"

    prompt = f"Context:\n{context}\n\nQuestion: {question}"

    token_count, _ = get_token_count(prompt)
    if token_count > 8192:
        raise ValueError("Prompt exceeds token limit.")

    cached_answer = cache.get(prompt)
    if cached_answer:
        return cached_answer

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
        )
        answer = response['choices'][0]['message']['content'].strip()
        cache.put(prompt, answer)
        return answer
    except Exception as e:
        raise RuntimeError(f"Error generating answer from OpenAI: {e}")

# Function to update the TestcaseAnswer in BigQuery
def update_testcase_answer_in_bigquery(task_id: str, validation_result: str):
    client = bigquery.Client(project=project_id)
    query = f"""
    UPDATE `{project_id}.{dataset_id}.{table_id}`
    SET TestcaseAnswer = @validation_result
    WHERE task_id = @task_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("validation_result", "STRING", validation_result),
            bigquery.ScalarQueryParameter("task_id", "STRING", task_id)
        ]
    )
    try:
        query_job = client.query(query, job_config=job_config)
        query_job.result()  # Wait for the query to finish
    except Exception as e:
        raise RuntimeError(f"Error updating TestcaseAnswer in BigQuery: {e}")

# Function to update the ValidationStepsAnswer in BigQuery
def update_validation_steps_answer_in_bigquery(task_id: str, validation_result: str):
    client = bigquery.Client(project=project_id)
    query = f"""
    UPDATE `{project_id}.{dataset_id}.{table_id}`
    SET ValidationStepsAnswer = @validation_result
    WHERE task_id = @task_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("validation_result", "STRING", validation_result),
            bigquery.ScalarQueryParameter("task_id", "STRING", task_id)
        ]
    )
    try:
        query_job = client.query(query, job_config=job_config)
        query_job.result()  # Wait for the query to finish
        print(f"Updated ValidationStepsAnswer for task_id {task_id} with {validation_result}")
    except Exception as e:
        raise RuntimeError(f"Error updating ValidationStepsAnswer in BigQuery: {e}")

# Main logic to integrate everything
if __name__ == "__main__":
    question, task_id = get_question_from_bigquery()
    annotator_metadata = get_annotator_metadata_from_bigquery(task_id)
    context = annotator_metadata['annotator_metadata']
    answer = get_openai_answer(question, context, annotator_metadata['gcs_file_path'])

    # Example usage of updating TestcaseAnswer and ValidationStepsAnswer in BigQuery
    testcase_validation_result = "True"  # Or "False" based on your logic
    steps_validation_result = "True"  # Or "False" based on your logic

    update_testcase_answer_in_bigquery(task_id, testcase_validation_result)
    update_validation_steps_answer_in_bigquery(task_id, steps_validation_result)
