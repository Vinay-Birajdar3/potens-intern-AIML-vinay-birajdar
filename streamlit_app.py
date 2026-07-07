import requests
import streamlit as st

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="PolicyLens",
    page_icon="📄",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000"

# ==========================================================
# CSS
# ==========================================================

st.markdown("""
<style>

#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}

.block-container{
    padding-top:2rem;
    padding-bottom:2rem;
    padding-left:3rem;
    padding-right:3rem;
}

/* Header */

.title{
    font-size:38px;
    font-weight:700;
}

.subtitle{
    color:#6B7280;
    font-size:16px;
    margin-top:-10px;
}

/* Answer Card */

.answer-card{

    background:#F8FAFC;

    border:1px solid #E5E7EB;

    border-radius:12px;

    padding:22px;

    line-height:1.8;

    font-size:16px;

}

/* Expander */

div[data-testid="stExpander"]{

    border-radius:12px !important;

    border:1px solid #E5E7EB !important;

    margin-bottom:10px;

}

/* Buttons */

.stButton>button{

    width:100%;

    background:#2563EB;

    color:white;

    border:none;

    border-radius:10px;

    height:46px;

    font-weight:600;

}

.stButton>button:hover{

    background:#1D4ED8;

    color:white;

}

/* Text Area */

textarea{

    border-radius:10px !important;

}

/* Select */

div[data-baseweb="select"]{

    border-radius:10px;

}

</style>
""", unsafe_allow_html=True)

# ==========================================================
# HEADER
# ==========================================================

col1, col2 = st.columns([8,2])

with col1:

    st.markdown(
        '<div class="title">📄 PolicyLens</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Enterprise Document Intelligence</div>',
        unsafe_allow_html=True
    )

with col2:

    try:

        requests.get(API_URL, timeout=2)

        st.success("🟢 Backend Online")

    except:

        st.error("🔴 Backend Offline")

st.divider()

# ==========================================================
# NAVIGATION
# ==========================================================

tab1, tab2, tab3 = st.tabs(
    [
        "💬 Ask Documents",
        "⚖️ Compare Documents",
        "ℹ️ About"
    ]
)

# ==========================================================
# ASK DOCUMENTS
# ==========================================================

with tab1:

    st.subheader("💬 Ask Documents")
    st.write("Ask questions about your enterprise documents.")

    question = st.text_area(
        "Question",
        placeholder="Example: Who does this policy apply to?",
        height=120
    )

    ask_btn = st.button("Ask AI")

    if ask_btn:

        if not question.strip():

            st.warning("Please enter a question.")

        else:

            with st.spinner("Searching documents..."):

                try:

                    response = requests.post(
                        f"{API_URL}/ask",
                        json={"question": question},
                        timeout=120
                    )

                    if response.status_code == 200:

                        result = response.json()

                        answer = result.get(
                            "answer",
                            "No answer generated."
                        )

                        citations = result.get(
                            "citations",
                            []
                        )

                        st.divider()

                        st.subheader("🧠 AI Response")

                        st.markdown(
                            f"""
<div class="answer-card">

{answer}

</div>
                            """,
                            unsafe_allow_html=True
                        )

                        st.write("")

                        st.subheader("📚 Citations")

                        if not citations:

                            st.info("No citations available.")

                        else:

                            for citation in citations[:4]:

                                source = citation.get(
                                    "source",
                                    "Unknown"
                                )

                                source = (
                                    source
                                    .replace("documents\\", "")
                                    .replace(".pdf", "")
                                    .replace("_", " ")
                                )

                                page = citation.get("page", "-")

                                snippet = citation.get(
                                    "snippet",
                                    ""
                                )

                                with st.expander(
                                    f"📄 {source}   •   Page {page}"
                                ):

                                    st.caption(
                                        "Supporting Document Excerpt"
                                    )

                                    st.markdown(
                                        f"""
> {snippet}
                                        """
                                    )

                    else:

                        st.error(
                            f"Backend Error ({response.status_code})"
                        )

                except Exception as e:

                    st.error(
                        f"Unable to connect to FastAPI.\n\n{e}"
                    )

# ==========================================================
# COMPARE DOCUMENTS
# ==========================================================

with tab2:

    st.subheader("⚖️ Compare Documents")

    documents = {
        "Employee Handbook": "employee_handbook",
        "Leave Policy": "leave_policy",
        "Work From Home Policy": "work_from_home",
        "Travel Expense Policy": "travel_policy",
        "Information Security Policy": "information_security",
        "Code of Conduct": "code_of_conduct"
    }

    col1, col2 = st.columns(2)

    with col1:

        document1 = st.selectbox(
            "Document 1",
            list(documents.keys())
        )

    with col2:

        document2 = st.selectbox(
            "Document 2",
            list(documents.keys()),
            index=1
        )

    topic = st.text_input(
        "Topic",
        placeholder="Example: Remote Work"
    )

    compare_btn = st.button("Compare Documents")

    if compare_btn:

        if document1 == document2:

            st.warning(
                "Please select two different documents."
            )

        elif not topic.strip():

            st.warning(
                "Please enter a topic."
            )

        else:

            with st.spinner("Comparing documents..."):

                try:

                    response = requests.post(

                        f"{API_URL}/contradict",

                        json={

                            "document1": documents[document1],
                            "document2": documents[document2],
                            "topic": topic

                        },

                        timeout=120

                    )

                    if response.status_code == 200:

                        result = response.json()["result"]

                        st.divider()

                        if result["conflict"]:

                            st.error("❌ Contradiction Found")

                        else:

                            st.success("✅ No Contradiction Found")

                        st.markdown(
                            f"""
<div class="answer-card">

<b>Reason</b>

<br><br>

{result["reason"]}

</div>
                            """,
                            unsafe_allow_html=True
                        )

                    else:

                        st.error("Backend Error.")

                except Exception as e:

                    st.error(
                        f"Unable to connect to FastAPI.\n\n{e}"
                    )


# ==========================================================
# ABOUT
# ==========================================================

with tab3:

    st.subheader("ℹ️ About PolicyLens")

    st.markdown("""
### Enterprise Document Intelligence

PolicyLens is a multilingual Retrieval-Augmented Generation (RAG) application for enterprise documents.

---

### Features

- 💬 Document Question Answering
- 📚 Citation-based Responses
- ⚖️ Contradiction Detection
- 🌍 English, Hindi & Marathi Support
- 🚫 Hallucination Prevention

---

### Technology Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| Backend | FastAPI |
| LLM | Groq (Llama 3.1) |
| Embeddings | all-MiniLM-L6-v2 |
| Vector Database | ChromaDB |
| Framework | LangChain |

---

### Workflow

1. User submits a question.
2. Relevant document chunks are retrieved.
3. Groq LLM generates a grounded response.
4. Supporting citations are returned.
""")