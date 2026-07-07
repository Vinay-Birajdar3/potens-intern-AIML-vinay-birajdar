import os

from groq import Groq

from app import config
from app.prompts import SYSTEM_PROMPT

client = Groq(
    api_key=config.GROQ_API_KEY
)


def generate_answer(question: str, retrieved_docs):
    """
    Generate a grounded answer from retrieved document chunks.
    """

    if not retrieved_docs:
        return {
            "answer": "The provided documents do not contain sufficient information.",
            "citations": []
        }

    context_parts = []
    citations = []

    for index, (doc, score) in enumerate(retrieved_docs, start=1):

        source = os.path.basename(doc.metadata.get("source", "Unknown"))

        page = doc.metadata.get("page", 0) + 1

        snippet = doc.page_content.strip()

        context_parts.append(
            f"""
Source: {source}
Page: {page}

Content:
{snippet}
"""
        )

        citations.append({
            "source": source,
            "page": page,
            "snippet": snippet[:250]
        })

    context = "\n\n-----------------------------\n\n".join(context_parts)

    user_prompt = f"""
Below are document excerpts retrieved from the knowledge base.

Your task is to answer the user's question ONLY using these excerpts.

Instructions:

• Read all retrieved document excerpts carefully.
• Identify only the information relevant to the question.
• Combine information when multiple excerpts support the answer.
• Rewrite the answer naturally instead of copying sentences.
• Keep the answer concise, professional and easy to understand.
• Never use outside knowledge.
• If the answer cannot be found in the retrieved context, reply exactly:

"The provided documents do not contain sufficient information."

-------------------------
RETRIEVED DOCUMENTS
-------------------------

{context}

-------------------------
USER QUESTION
-------------------------

{question}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    answer = response.choices[0].message.content.strip()

    return {
        "answer": answer,
        "citations": citations
    }