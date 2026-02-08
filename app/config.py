import os
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 1. Critical Reasoning Model (Gap Analysis) - High Intelligence
# Note: Use with caution due to 6k TPM limit on free tier.
llm_reasoning = ChatGroq(
    temperature=0,
    model_name="llama-3.3-70b-versatile",
    groq_api_key=GROQ_API_KEY
)

# 2. Fast Extraction Model (Parsing/summarizing) - High Speed
llm_fast = ChatGroq(
    temperature=0,
    model_name="llama-3.1-8b-instant",
    groq_api_key=GROQ_API_KEY
)

# 3. Embeddings (Local - No Rate Limits)
# We use a solid HF model to handle retrieval locally
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")