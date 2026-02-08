# app/vector_store.py
from langchain_community.vectorstores import FAISS
from app.config import embeddings

def create_vector_store(chunks):
    """
    Creates an in-memory FAISS vector store for the Internal Policy.
    """
    vector_store = FAISS.from_documents(chunks, embeddings)
    return vector_store