# 📄 PolicyLens – Enterprise Document Intelligence using RAG

PolicyLens is a multilingual **Retrieval-Augmented Generation (RAG)** application that enables users to interact with enterprise policy documents using natural language. The system retrieves semantically relevant document chunks from a vector database, generates grounded responses using **Groq Llama 3.1**, and provides source citations to improve transparency and reduce hallucinations.

In addition to document question answering, PolicyLens supports multilingual queries, document contradiction detection, and automated RAG evaluation using **DeepEval**.

---

# ✨ Features

- 📄 Enterprise Document Question Answering
- 📚 Citation-based Responses
- 🌍 Multilingual Support (English, Hindi & Marathi)
- ⚖️ Document Contradiction Detection
- 🚫 Grounded Responses to Reduce Hallucinations
- 🤖 Groq (Llama 3.1) Integration
- 🗂️ ChromaDB Vector Database
- 📊 DeepEval-based RAG Evaluation
- 💻 FastAPI REST API
- 🖥️ Streamlit Web Interface
- 🐳 Docker Support

---

# 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI |
| Frontend | Streamlit |
| Framework | LangChain |
| LLM | Groq (Llama 3.1-8B Instant) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector Database | ChromaDB |
| PDF Processing | PyPDF |
| Translation | Deep Translator |
| Language Detection | LangDetect |
| Evaluation | DeepEval |
| Containerization | Docker |

---

# 🏗️ System Architecture

```text
                    User Query
                         │
                         ▼
              Language Detection
                         │
            (Translate if Required)
                         │
                         ▼
              ChromaDB Retrieval
                         │
                         ▼
         Relevant Document Chunks
                         │
                         ▼
             Groq Llama 3.1 LLM
                         │
                         ▼
        Grounded Answer + Citations
                         │
                         ▼
              DeepEval Evaluation
```

---

# 📂 Project Structure

```text
potens-intern-ai-vinay/
│
├── app/
│   ├── api.py
│   ├── config.py
│   ├── contradiction.py
│   ├── deepeval_integration.py
│   ├── evaluation.py
│   ├── ingest.py
│   ├── main.py
│   ├── prompts.py
│   ├── rag.py
│   ├── retrieval.py
│   ├── translation.py
│   ├── utils.py
│   └── __init__.py
│
├── chroma_db/
├── documents/
├── tests/
│   └── test_evaluation.py
│
├── streamlit_app.py
├── run_deepeval.py
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── requirements.txt
├── README.md
└── .env
```

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/Vinay-Birajdar3/potens-intern-AIML-vinay-birajdar.git

cd potens-intern-ai-vinay
```

---

## 2. Create a Virtual Environment

```bash
python -m venv .venv
```

### Activate the Environment

**Windows**

```bash
.venv\Scripts\activate
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file in the project root.

```env
GROQ_API_KEY=YOUR_GROQ_API_KEY

MODEL_NAME=llama-3.1-8b-instant

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

CHROMA_DB_PATH=./chroma_db

DOCUMENTS_PATH=./documents

DEEPEVAL_GROQ_MODEL=llama-3.1-8b-instant
```

---

# 📚 Build the Vector Database

Generate embeddings and store them in ChromaDB.

```bash
python -m app.ingest
```

This process:

- Loads PDF documents
- Splits documents into semantic chunks
- Generates vector embeddings
- Stores vectors in ChromaDB

---

# 🚀 Running the Application

## Start FastAPI Backend

```bash
uvicorn app.main:app --reload
```

Swagger Documentation

```text
http://127.0.0.1:8000/docs
```

---

## Start Streamlit Frontend

```bash
streamlit run streamlit_app.py
```

Open

```text
http://localhost:8501
```

---

# 🐳 Run with Docker

Build and start both backend and frontend using Docker Compose.

```bash
docker-compose up --build
```

---

# 📡 API Endpoints

## `POST /ask`

Retrieves relevant information from indexed documents and generates a grounded response with supporting citations.

### Request

```json
{
  "question": "Who is responsible for approving business travel?"
}
```

### Response

```json
{
  "answer": "Business travel requires prior approval from the reporting manager.",
  "citations": [
    {
      "source": "travel_policy.pdf",
      "page": 5,
      "snippet": "Business travel requires prior approval..."
    }
  ]
}
```

---

## `POST /contradict`

Compares two enterprise policy documents and identifies contradictions for a given topic.

### Request

```json
{
  "document1": "employee_handbook",
  "document2": "leave_policy",
  "topic": "Leave Approval"
}
```

### Response

```json
{
  "conflict": true,
  "reason": "The approval process differs between the two documents."
}
```

---

# 📊 DeepEval RAG Evaluation

PolicyLens includes an automated evaluation pipeline built using **DeepEval** to measure the quality of Retrieval-Augmented Generation (RAG) responses.

The evaluation runs independently from the production API using a benchmark dataset (golden questions).

### Metrics Evaluated

- ✅ Answer Relevancy
- ✅ Faithfulness
- ✅ Contextual Precision
- ✅ Contextual Recall

Run the evaluation:

```bash
python run_deepeval.py
```

Results are generated in:

```text
deepeval_report.json
```

The evaluation follows an **LLM-as-a-Judge** approach where an LLM evaluates the generated answer against the retrieved context and expected response.

---

# 🧪 Testing

Run project tests:

```bash
pytest tests/
```

Run RAG evaluation:

```bash
python run_deepeval.py
```

---

# 🔄 RAG Workflow

```text
                 User Question
                       │
                       ▼
            Language Detection
                       │
        Translate (if required)
                       │
                       ▼
          ChromaDB Similarity Search
                       │
                       ▼
        Relevant Document Chunks
                       │
                       ▼
            Groq (Llama 3.1)
                       │
                       ▼
       Grounded Answer + Citations
                       │
                       ▼
            DeepEval Evaluation
```

---

# 🌍 Multilingual Support

Supported Languages

- English
- Hindi
- Marathi

### Processing Pipeline

1. Detect input language.
2. Translate to English (if required).
3. Retrieve relevant document chunks.
4. Generate a grounded answer.
5. Translate the response back to the user's language.

---

# 🚫 Hallucination Prevention

PolicyLens minimizes hallucinations by following a **retrieval-first** architecture.

- Answers are generated only from retrieved document context.
- Every response includes supporting citations.
- External knowledge is not used while answering document-specific questions.
- If supporting evidence is unavailable, the system returns:

> **"The provided documents do not contain sufficient information."**

---

# 🚀 Future Improvements

- Hybrid Search (BM25 + Dense Retrieval)
- Cross-Encoder Re-ranking
- Confidence Score for Responses
- Conversation Memory
- Document Upload Support
- Authentication & Authorization
- LangSmith Observability
- CI/CD Evaluation Pipeline
- Kubernetes Deployment

---

# 📝 Project Summary

PolicyLens is an enterprise document intelligence system built using a **Retrieval-Augmented Generation (RAG)** architecture. Enterprise policy documents are parsed, chunked using LangChain's `RecursiveCharacterTextSplitter`, embedded using the `sentence-transformers/all-MiniLM-L6-v2` model, and stored in **ChromaDB** for semantic retrieval.

During querying, the application retrieves the most relevant document chunks before generating grounded responses using **Groq Llama 3.1**, ensuring that every answer is supported by retrieved evidence and accompanied by source citations.

Beyond document question answering, the project provides:

- 🌍 Multilingual document querying
- ⚖️ Policy contradiction detection
- 📚 Citation-based responses
- 📊 DeepEval-powered RAG evaluation

The evaluation pipeline measures answer quality using metrics such as **Answer Relevancy**, **Faithfulness**, **Contextual Precision**, and **Contextual Recall**, helping validate the reliability of the RAG system.

---

# 📌 Key Highlights

- Enterprise Document Intelligence
- Retrieval-Augmented Generation (RAG)
- Semantic Search using ChromaDB
- Groq Llama 3.1 Integration
- DeepEval-based RAG Evaluation
- FastAPI REST API
- Streamlit Frontend
- Multilingual Support
- Citation-based Responses
- Docker Support

---

# 👨‍💻 Author

**Vinay Birajdar**

**Bachelor of Engineering – Artificial Intelligence & Data Science**


**GitHub**  
https://github.com/Vinay-Birajdar3

**LinkedIn**  
https://www.linkedin.com/in/vinay-birajdar-240b642b7

---

⭐ If you found this project useful, consider giving the repository a star!
