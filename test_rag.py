from app.retrieval import retrieve_documents
from app.rag import generate_answer

question = "How many annual leaves are provided?"

retrieved_docs = retrieve_documents(question)

response = generate_answer(question, retrieved_docs)

print("\nANSWER\n")
print(response["answer"])

print("\nCITATIONS\n")

for citation in response["citations"]:
    print(citation)