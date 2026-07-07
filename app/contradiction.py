import json

from groq import Groq
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app import config

embedding_model = HuggingFaceEmbeddings(
    model_name=config.EMBEDDING_MODEL
)

client = Groq(api_key=config.GROQ_API_KEY)

# Mapping between document IDs and actual PDF names
DOCUMENT_MAP = {
    "employee_handbook": "Employee_Handbook.pdf",
    "leave_policy": "Leave_Policy.pdf",
    "work_from_home": "Work_From_Home_Policy.pdf",
    "travel_policy": "Travel_Expense_Policy.pdf",
    "information_security": "Information_Security_Policy.pdf",
    "code_of_conduct": "Code_of_Conduct.pdf",
}


def check_contradiction(document1: str, document2: str, topic: str):
    """
    Compare two documents on a specific topic and determine
    whether they contradict each other.
    """

    db = Chroma(
        persist_directory=config.CHROMA_DB_PATH,
        embedding_function=embedding_model
    )

    pdf1 = DOCUMENT_MAP.get(document1)
    pdf2 = DOCUMENT_MAP.get(document2)

    if not pdf1 or not pdf2:
        return {
            "conflict": False,
            "reason": "Invalid document ID."
        }

    docs1 = db.similarity_search(
        query=topic,
        k=5,
        filter={"source": f"documents\\{pdf1}"}
    )

    docs2 = db.similarity_search(
        query=topic,
        k=5,
        filter={"source": f"documents\\{pdf2}"}
    )

    context1 = "\n\n".join(doc.page_content for doc in docs1)
    context2 = "\n\n".join(doc.page_content for doc in docs2)

    prompt = f"""
Compare ONLY the supplied document excerpts.

Topic:
{topic}

--------------------------------

Document 1 ({document1})

{context1}

--------------------------------

Document 2 ({document2})

{context2}

Determine whether the two documents contradict each other regarding the given topic.

Return ONLY valid JSON.

Example:

{{
    "conflict": true,
    "reason": "Short explanation."
}}

or

{{
    "conflict": false,
    "reason": "Short explanation."
}}

Do not include markdown.
Do not include ```json.
Do not use outside knowledge.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are a document comparison assistant. Always return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response.choices[0].message.content.strip()

    # Remove markdown if the model accidentally returns it
    content = content.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(content)

    except json.JSONDecodeError:
        return {
            "conflict": False,
            "reason": content
        }