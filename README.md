# Potens Intern AI

This project scaffold includes:

- A FastAPI app in the app package
- A Streamlit UI entry point
- Placeholder modules for ingestion, retrieval, RAG, translation, and contradiction handling
- A documents folder and a Chroma vector DB folder

## Run locally

1. Create and activate a virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Start the API: `uvicorn app.main:app --reload`
4. Start the UI: `streamlit run streamlit_app.py`
