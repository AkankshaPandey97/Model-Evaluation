# Model Evaluation System

## Live Application Links
- **Streamlit Application**: [Streamlit URL Here](http://your-streamlit-url)

## Problem Statement
Build an interactive tool for evaluating OpenAI models using specific test cases sourced from the GAIA dataset.

## Project Goals
- Allow users to select validation test cases and submit queries to the OpenAI model.
- Facilitate comparison of OpenAI responses with correct answers from the metadata.
- Capture insights to improve model performance.

## Technologies Used
- GitHub
- Python
- OpenAI API
- Google Cloud Platform (GCP)
- Streamlit
- BigQuery

## Pre-requisites
- Knowledge of Python
- OpenAI API Key
- Google Cloud Platform account
- Familiarity with Streamlit
- Understanding of BigQuery


## How to Run the Application Locally
1. Clone the repository:
   ```bash
   git clone https://github.com/your_username/Model-Evaluation-System.git
   cd Model-Evaluation-System
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
| Kalash Desai                | 33.3%          | Architecture design, Streamlit app development     |
| Akanksha Pandey             | 33.3%          | OpenAI integration, feedback processing            |
| Sai Pranavi Jeedigunta      | 33.3%          | Data retrieval from GCP, metadata management       |
