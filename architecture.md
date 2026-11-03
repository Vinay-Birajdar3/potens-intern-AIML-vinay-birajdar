# PolicyLens architecture (plain-language guide)

## What the app does

PolicyLens answers questions using the policy PDFs added to its document
library. It searches those documents first, then asks a language model to write
an answer based on the matching text. The answer includes citations so you can
check the original policy.

This design is called **Retrieval-Augmented Generation (RAG)**:

- **Retrieval** finds useful passages in the PDFs.
- **Augmented** means those passages are given to the language model.
- **Generation** is the answer the model writes from that supplied evidence.

## How a policy document becomes searchable

```text
PDF and Markdown files in documents/
        |
        v
PyPDF reads PDF pages; the text loader reads Markdown files
        |
        v
LangChain splits the text into small, overlapping chunks
        |
        v
Sentence Transformers turns each chunk into a vector (a list of numbers)
        |
        v
ChromaDB saves the vectors and source/page details
```

In normal use, the index is built once and reused. To rebuild it after changing
or adding policy files, run:

```bash
docker compose run --rm backend python -m app.ingest
```

Stop the backend before rebuilding the index, then restart it so it reconnects
to the new index.

## What happens when someone asks a question

```text
Person
  |
  v
React website
  |
  v
Nginx forwards the request to FastAPI
  |
  v
Language check
  | English: use the question as-is
  | Hindi/Marathi: translate the question into English for document search
  v
Sentence Transformer converts the question to a vector
  |
  v
ChromaDB finds the closest policy chunks
  |
  v
Keep close, non-duplicate chunks and their source/page details
  |
  v
Groq language model writes a short answer using only those chunks
  |
  v
Website shows the answer and citations
  |
  +---- DeepEval checks the answer in the background and updates Excel
```

The answer prompt asks the model to respond in the question's language. If
there is no useful evidence, PolicyLens returns a “not enough information”
message instead of making up a policy answer.

## How policy comparison works

When you compare two policies, PolicyLens searches ChromaDB separately for
useful passages from each selected policy. Groq compares those passages for the
topic you entered and returns whether they appear to conflict, with a short
reason. If it cannot find passages from both policies, it reports that there
is not enough information to compare them.

## Libraries and services

| Library or service | What it does in PolicyLens |
|---|---|
| **React** | Builds the interactive question-and-answer and policy comparison website. |
| **Vite** | Builds the React website files for deployment. |
| **Nginx** | Serves the built website and forwards API requests to FastAPI. It keeps the API key out of the browser. |
| **FastAPI** | Provides the API endpoints used by the website, including `/ask` and `/contradict`. |
| **Uvicorn** | Runs the FastAPI application as a web server. |
| **Groq** | Provides the language model used for language detection, translation, grounded answers, and policy comparison. |
| **Sentence Transformers** | Uses `all-MiniLM-L6-v2` to convert document text and questions into vectors for meaning-based search. |
| **LangChain** | Connects the PDF loader, text splitter, embeddings, and Chroma vector database. |
| **PyPDF / PyPDFDirectoryLoader** | Reads PDF pages and their text during indexing. |
| **LangChain TextLoader / DirectoryLoader** | Reads the Markdown policy files in `documents/` during indexing. |
| **ChromaDB** | Stores document vectors and finds chunks that are semantically similar to a question. |
| **DeepEval** | Evaluates answer faithfulness, answer relevancy, and context relevancy after the answer is returned. |
| **openpyxl** | Writes the latest evaluation results to the Excel workbook. |
| **Docker Compose** | Runs the website and API as separate containers and connects them. |

## Techniques used

| Technique | In simple terms |
|---|---|
| **Chunking with overlap** | Breaks long pages into smaller passages. A little repeated text between passages helps keep sentences and ideas together. |
| **Semantic/vector search** | Finds text by meaning, not only by exact word matches. |
| **Top-k retrieval** | Searches a shortlist of likely passages, then uses a small number of the best ones as evidence. |
| **Distance threshold** | Rejects search results whose similarity distance is too high; lower distances are closer matches. |
| **Duplicate filtering** | Avoids giving repeated passages to the answer model. |
| **Grounded generation** | Tells the model to use only the retrieved policy text, not outside knowledge. |
| **Abstention** | Returns a clear “not enough information” answer when the documents do not support a response. |
| **Citations** | Shows the source PDF, page, and text snippet used for the answer. |
| **Startup warmup** | Loads the embedding model and vector index before the API reports ready, avoiding a long first search. |
| **Answer cache** | Reuses an answer only when the exact grounded prompt (including its retrieved evidence and answer language) matches. |
| **Background evaluation** | Sends the answer first; evaluation and Excel writing happen afterward so they do not hold up the response. |

## Main project files

| File or folder | Purpose |
|---|---|
| `documents/` | Policy PDF and Markdown files that are indexed. The added Markdown policies are samples for testing, not official company rules. |
| `app/ingest.py` | Reads PDFs, splits them into chunks, and builds the Chroma index. |
| `app/retrieval.py` | Loads and warms up the embedding model and searches ChromaDB. |
| `app/translation.py` | Detects English, Hindi, or Marathi and translates non-English questions for searching. |
| `app/rag.py` | Builds the evidence-based answer prompt, adds citations, and caches exact repeated prompts. |
| `app/api.py` | Defines question, evaluation-status, and policy-comparison API routes. |
| `app/evaluation.py` | Runs background DeepEval scoring and updates the Excel report. |
| `frontend/src/` | React website source code. |
| `docker-compose.yml` | Starts and connects the frontend and backend containers. |

The added sample policies cover code of conduct, respect at work and equal
opportunity, data privacy and retention, employee benefits and wellbeing,
procurement and vendors, incident response and business continuity, conflicts
of interest, and remote-work equipment. Existing PDF policies for the employee
handbook, leave, travel expenses, information security, and working from home
remain in the library.

## Useful local addresses

With the default Docker Compose settings:

- Website: `http://localhost:8501`
- API documentation: `http://localhost:8000/docs`

If another application already uses port `8000`, set `BACKEND_PORT=8001` in
your shell before starting Compose; the website continues to use port `8501`.
