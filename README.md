# Model Evaluation System

## Live Application Links
- **Streamlit Application**: [Streamlit URL Here](http://your-streamlit-url)

## Problem Statement
Build an interactive tool for evaluating OpenAI models using specific test cases from the GAIA dataset.

## Project Goals
- Allow users to select validation test cases and submit queries to the OpenAI model.
- Facilitate comparison of OpenAI responses with correct answers from the metadata.
- Capture insights to improve model performance.

## Technologies Used
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/)
[![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-0A0A0A?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
[![Google Cloud Platform](https://img.shields.io/badge/Google%20Cloud%20Platform-%234285F4.svg?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![BigQuery](https://img.shields.io/badge/BigQuery-0072C6?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com/bigquery)
[![Google Cloud Storage](https://img.shields.io/badge/Google%20Cloud%20Storage-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com/storage)

## Pre-requisites
- Knowledge of Python
- OpenAI API Key
- Google Cloud Platform account
- Familiarity with Streamlit
- Understanding of BigQuery

## Architecture Diagram
![Architecture Diagram](https://github.com/BigDataIA-Fall2024-TeamA7/Assignment-1/blob/main/architecture-diagram/architecture_diagram.png)

## Demo Video

You can view the demo video by clicking [here](https://github.com/BigDataIA-Fall2024-TeamA7/Assignment-1/blob/main/demo/938d3e14-9a83-479f-ae16-28cdb8d3f8e7.MP4).

## How to Run the Application Locally
1. Clone the repository:
   ```bash
   git clone https://github.com/BigDataIA-Fall2024-TeamA7/Assignment-1.git
   cd Assignment-1
   ```
   
2. Navigate to each folder where `requirements.txt` is present:
   ```bash
   cd streamlit_app
   pip install -r requirements.txt
   ```

3. Set up configuration files:
   - Create a `.env` file and add your credentials for GCP and OpenAI API.

4. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

5. Run the Streamlit application:
   ```bash
   streamlit run main.py
   ```

## References
- [GAIA Dataset](https://huggingface.co/datasets/gaia-benchmark/GAIA)
- [OpenAI API](https://openai.com/api/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Google Cloud Platform](https://cloud.google.com/)

## Team Contributions
| Name                        | Contribution % | Contributions                                      |
|---------------------------  |----------------|----------------------------------------------------|
| Kalash Desai                | 33.3%          | Streamlit app development                          |
| Akanksha Pandey             | 33.3%          | Data retrieval from GCP, metadata management       |
| Sai Pranavi Jeedigunta      | 33.3%          | Integrated OpenAI API with BigQuery and Streamlit  |
