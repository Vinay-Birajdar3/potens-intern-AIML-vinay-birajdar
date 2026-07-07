# 📄 PolicyLens – Enterprise Document Intelligence (RAG)

PolicyLens is a multilingual **Retrieval-Augmented Generation (RAG)** system that enables users to query enterprise policy documents using natural language. It retrieves relevant information from indexed documents, generates grounded responses using an LLM, and returns supporting citations to ensure transparency and minimize hallucinations.

---

## ✨ Features

* 📄 Document Question Answering using RAG
* 📚 Citation-based responses (Source, Page & Supporting Snippet)
* ⚖️ Document Contradiction Detection
* 🌍 Multilingual Support (English, Hindi & Marathi)
* 🚫 Hallucination Prevention
* 💻 FastAPI REST API
* 🖥️ Streamlit User Interface
* 🗂️ ChromaDB Vector Database
* 🤖 Groq LLM Integration

---

## 🛠️ Tech Stack

| Component          | Technology                             |
| ------------------ | -------------------------------------- |
| Backend            | FastAPI                                |
| Frontend           | Streamlit                              |
| Framework          | LangChain                              |
| LLM                | Groq (Llama 3.1)                       |
| Embeddings         | sentence-transformers/all-MiniLM-L6-v2 |
| Vector Database    | ChromaDB                               |
| PDF Loader         | PyPDF                                  |
| Translation        | Deep Translator                        |
| Language Detection | LangDetect                             |

---

## 📂 Project Structure

```text
potens-intern-ai-vinay/

│
├── app/
│   ├── api.py
│   ├── config.py
│   ├── contradiction.py
│   ├── ingest.py
│   ├── main.py
│   ├── prompts.py
│   ├── rag.py
│   ├── retrieval.py
│   └── translation.py
│
├── documents/
├── streamlit_app.py
├── requirements.txt
├── README.md
└── .env
```

---

# ⚙️ Setup

## 1. Clone Repository

```bash
git clone https://github.com/Vinay-Birajdar3/potens-intern-AIML-vinay-birajdar.git

cd potens-intern-ai-vinay
```

---

## 2. Create Virtual Environment

```bash
python -m venv .venv
```

### Activate

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

## 4. Create `.env`

```env
GROQ_API_KEY=YOUR_GROQ_API_KEY

MODEL_NAME=llama-3.1-8b-instant

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

CHROMA_DB_PATH=./chroma_db

DOCUMENTS_PATH=./documents
```

---

# 📚 Build Vector Database

Run:

```bash
python -m app.ingest
```

This will:

* Load PDF documents
* Split documents into chunks
* Generate embeddings
* Store vectors in ChromaDB

---

# 🚀 Run FastAPI

```bash
uvicorn app.main:app --reload
```

Swagger Documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 🖥️ Run Streamlit

```bash
streamlit run streamlit_app.py
```

---

# 📡 API Endpoints

## POST `/ask`

Ask questions from the indexed documents.

### Request

```json
{
  "question": "Who does this policy apply to?"
}
```

### Returns

* Answer
* Source Document
* Page Number
* Supporting Snippet

---

## POST `/contradict`

Compare two documents for contradictions on a given topic.

### Request

```json
{
  "document1": "employee_handbook",
  "document2": "leave_policy",
  "topic": "Leave Approval"
}
```

### Returns

* Conflict Status
* Reason

---

# 🧩 Chunking Strategy

Documents are split using **LangChain RecursiveCharacterTextSplitter**.

### Configuration

* **Chunk Size:** 1000 characters
* **Chunk Overlap:** 200 characters

### Why this strategy?

* Preserves context across chunk boundaries.
* Improves semantic retrieval quality.
* Prevents important information from being split abruptly.
* Produces meaningful context while keeping prompts efficient.

Each chunk stores metadata including:

* Source Document
* Page Number

These metadata are later returned as citations.

---

# 📚 Citation Strategy

Every generated answer includes:

* Source Document
* Page Number
* Supporting Snippet

This allows users to verify every answer against the original document, ensuring transparency and trustworthiness.

---

# 🌍 Multilingual Support

Supported Languages:

* English
* Hindi
* Marathi

### Workflow

1. Detect query language.
2. Translate to English (if required).
3. Retrieve relevant document chunks.
4. Generate grounded answer.
5. Translate the response back to the user's language.

---

# 🚫 Hallucination Prevention

The system follows a retrieval-first approach to minimize hallucinations.

* Answers are generated **only** from retrieved document context.
* External knowledge is not used.
* If the requested information is unavailable, the system explicitly responds:

> **"The provided documents do not contain sufficient information."**

---

# 🔄 System Workflow

1. User submits a question.
2. Documents are searched using vector similarity.
3. Relevant chunks are retrieved from ChromaDB.
4. Groq LLM generates an answer using only the retrieved context.
5. The answer is returned along with supporting citations.

---

# 🚀 Future Improvements

* Hybrid Search (BM25 + Dense Retrieval)
* Confidence Score
* Cross-Encoder Re-ranking
* User Authentication
* Conversation Memory
* Document Upload
* Docker Deployment
* Production Logging & Monitoring

---

# 📝 Approach Summary

PolicyLens implements a Retrieval-Augmented Generation (RAG) pipeline for enterprise document question answering. PDF documents are parsed, divided into overlapping chunks using LangChain's RecursiveCharacterTextSplitter, embedded using the `all-MiniLM-L6-v2` model, and stored in ChromaDB. During querying, the system retrieves the most relevant chunks before passing them to the Groq LLM, ensuring responses are grounded only in retrieved context. The application supports multilingual queries, citation-based responses, contradiction detection between documents, and explicit fallback responses when supporting evidence is unavailable, reducing hallucinations while improving answer reliability.

---

# ✅ Assignment Checklist

* ✔️ Ingest, Chunk, Embed & Store Documents
* ✔️ Explained Chunking Strategy
* ✔️ `/ask` Endpoint with Citations
* ✔️ `/contradict` Endpoint
* ✔️ Multilingual Query Support
* ✔️ Streamlit User Interface
* ✔️ Hallucination Prevention
* ✔️ ChromaDB Vector Store
* ✔️ Groq LLM Integration

---

# 🤖 AI Use Log

| AI Tool              |         Approximate Usage | Purpose                                                                                                                                                                                                                                              |
| -------------------- | ------------------------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **ChatGPT (OpenAI)** |         ~300–400 messages | Assisted with project architecture, RAG pipeline design, FastAPI implementation, Streamlit UI development, multilingual support, contradiction detection, debugging, prompt engineering, documentation, README preparation, and deployment guidance. |
| **GitHub Copilot**   | ~100–150 code completions | Assisted with boilerplate code generation, import suggestions, repetitive code completion, syntax assistance, and improving development productivity during implementation.                                                                          |

**Declaration:** AI tools were used to accelerate development, debugging, and documentation. All architectural decisions, code integration, testing, validation, and the final implementation were completed and verified by the project author.


---

# 👨‍💻 Author

**Vinay Birajdar**

AI/ML Engineering Internship Assignment

**Potens IT Services and Consultancy Pvt. Ltd. (2026)**
