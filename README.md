# 📄 PolicyLens – Enterprise Document Intelligence (RAG)

PolicyLens is a multilingual **Retrieval-Augmented Generation (RAG)** system that enables users to query enterprise policy documents using natural language. It retrieves relevant information from indexed documents, generates grounded responses using an LLM, and returns supporting citations to ensure transparency and minimize hallucinations.

---

## ✨ Features

* 📄 Document Question Answering using RAG
* 📚 Citation-based responses (Source, Page & Supporting Snippet)
* ⚖️ Document Contradiction Detection
* 🌍 Multilingual Support (English, Hindi & Marathi)
* 🛡️ Grounded answers with abstention when no relevant context is found
* 💻 FastAPI REST API
* 🖥️ Minimal React User Interface
* 🗂️ ChromaDB Vector Database
* 🤖 Groq LLM Integration

---

## 🛠️ Tech Stack

| Component          | Technology                             |
| ------------------ | -------------------------------------- |
| Backend            | FastAPI                                |
| Frontend           | React, Vite, Nginx                     |
| Framework          | LangChain                              |
| LLM                | Groq                                    |
| Embeddings         | sentence-transformers/all-MiniLM-L6-v2 |
| Vector Database    | ChromaDB                               |
| PDF Loader         | PyPDF                                  |
| Translation        | Groq                                    |
| Language Detection | ASCII fast path + Groq for other scripts |

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
├── frontend/
│   ├── src/
│   ├── package.json
│   └── nginx.conf.template
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

For the test suite, DeepEval, and optional Ragas checks, install
`requirements.dev.txt` instead.

Run the unit tests with:

```bash
python -m pytest -q tests
```

---

## 4. Create `.env`

```env
GROQ_API_KEY=YOUR_GROQ_API_KEY
APP_ENV=development
APP_API_KEY=
GROQ_MODEL=openai/gpt-oss-20b
LIVE_EVALUATION_ENABLED=false

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

# 🖥️ Run the React UI locally

```bash
cd frontend
npm ci
npm run dev
```

The Vite development server hosts the UI at `http://localhost:5173`. To use it
outside Compose, configure a development proxy for the API or run the UI with
the production Nginx container.

---

# Docker

Docker Compose runs the FastAPI backend and React frontend together. Create
the `.env` file from `.env.example`, add your Groq API key, then start the
application from the project directory:

```bash
cp .env.example .env
docker compose up --build
```

On PowerShell, use `Copy-Item .env.example .env` for the first command.

Open the UI at `http://localhost:8501` and the API documentation at
`http://localhost:8000/docs`. The Nginx frontend proxies API requests to the Docker backend and keeps
`APP_API_KEY` out of browser code.

The backend warms the local embedding model and vector index before reporting
ready. A first deployment may take longer to start while model weights are
loaded or downloaded, but that setup time is kept out of the first search.

The existing `./chroma_db` directory is mounted into the backend container, so
indexed documents persist across rebuilds. Compose points the new index to
`./chroma_db/index` and continues to read the existing root-level index until
the new one has been built. Ingestion stages the new index on the same mounted
volume and switches to it only after a successful build. Stop the backend
before reindexing, then restart it so it reconnects to the new database:

```bash
docker compose run --rm backend python -m app.ingest
```

Run the optional DeepEval suite in a one-off container with:

```bash
docker compose --profile evaluation run --rm evaluation
```

Stop the stack with:

```bash
docker compose down
```

---

# DeepEval RAG evaluation

DeepEval evaluates every live answer in the background using LLM-as-a-judge
metrics for answer relevancy, faithfulness, and contextual relevancy. Golden
answers also enable contextual precision and recall. Live scoring makes
additional paid model calls but does not delay delivery of the answer. The
latest 100 results are written as an Excel workbook outside the project to
`../rag-evaluations/rag_evaluation_report.xlsx` (or the configured
`RAG_EVAL_REPORT_PATH`).

```bash
pip install -r requirements.evaluation.txt
python run_deepeval.py
```

Set `DEEPEVAL_GROQ_MODEL` in `.env` to override the default judge model.
The standalone golden-set run updates the same external report.

## Production deployment

- Set `APP_ENV=production` and set `APP_API_KEY` to a unique, high-entropy
  secret of at least 32 characters.
  `/ask` and `/contradict` require `Authorization: Bearer <APP_API_KEY>`.
- Configure request rate limits at the reverse proxy; the API key and Uvicorn
  concurrency limit are not a substitute for per-client rate limiting.
- Use a deployment secret manager to inject `GROQ_API_KEY` and `APP_API_KEY`;
  do not commit `.env` or expose these values to browser-side code.
- Compose binds the UI and API to `127.0.0.1` by default. Put a TLS-terminating
  reverse proxy in front of the frontend; do not expose the development ports
  directly to the public internet. Configure `FRONTEND_BIND_ADDRESS` and
  `BACKEND_BIND_ADDRESS` only when your network boundary requires it.
- Serving containers run as an unprivileged user with a read-only root filesystem.
  On Linux hosts, make the `chroma_db` bind mount writable by UID/GID 10001.
- `/health/live` checks process liveness and `/health/ready` verifies the API
  key configuration and a populated vector index. The vector database and
  source PDFs contain sensitive company data; restrict their host permissions
  and backups.
- Retrieval distance is a configurable Chroma distance cutoff, not a calibrated
  probability of correctness. Validate `MAX_RETRIEVAL_DISTANCE`, chunking, and
  top-k settings against a representative golden-question set before changing
  them. Rebuild the index after changing the embedding model or chunk settings.
- This Compose setup is a single-node deployment using a local Chroma database.
  Do not scale multiple backend replicas against the same SQLite volume; use a
  server-backed vector database and shared rate limiting for a multi-instance
  deployment.

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

* **Chunk Size:** 800 characters
* **Chunk Overlap:** 150 characters

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

# 🛡️ Grounding and Abstention

The system reduces unsupported answers with retrieval filtering and explicit
abstention rules. No generative model can guarantee zero hallucinations.

* Answers are generated **only** from retrieved document context.
* External knowledge is not used.
* If the requested information is unavailable, the system explicitly responds:

> **"The provided documents do not contain sufficient information."**

---

# 🔄 System Workflow

1. User submits a bounded question.
2. English input skips remote language detection; other input is detected and translated when needed.
3. ChromaDB retrieves candidate chunks, then distance filtering and duplicate removal are applied.
4. Groq generates a concise answer in the user's language using only the retained context.
5. If no context passes the retrieval cutoff, the API abstains without an LLM call.

---

# 🚀 Future Improvements

* Hybrid Search (BM25 + Dense Retrieval)
* Confidence Score
* Cross-Encoder Re-ranking
* Conversation Memory
* Document Upload
* Distributed rate limiting and production metrics

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
* ✔️ React User Interface
* ✔️ Grounded answers with abstention when evidence is insufficient
* ✔️ ChromaDB Vector Store
* ✔️ Groq LLM Integration

---

# 🤖 AI Use Log

| AI Tool              |         Approximate Usage | Purpose                                                                                                                                                                                                                                              |
| -------------------- | ------------------------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **ChatGPT (OpenAI)** |         ~300–400 messages | Assisted with project architecture, RAG pipeline design, FastAPI implementation, React UI development, multilingual support, contradiction detection, debugging, prompt engineering, documentation, README preparation, and deployment guidance. |
| **GitHub Copilot**   | ~100–150 code completions | Assisted with boilerplate code generation, import suggestions, repetitive code completion, syntax assistance, and improving development productivity during implementation.                                                                          |

**Declaration:** AI tools were used to accelerate development, debugging, and documentation. All architectural decisions, code integration, testing, validation, and the final implementation were completed and verified by the project author.


---

# 👨‍💻 Author

**Vinay Birajdar**

AI/ML Engineering Internship Assignment

**Potens IT Services and Consultancy Pvt. Ltd. (2026)**
