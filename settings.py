import os
from dotenv import load_dotenv

OPENAI_API_KEY = None
PINECONE_API_KEY = None
PINECONE_ENVIRONMENT = None

# task tree settings
MAX_TREE_DEPTH = 3

def project_init():
    load_dotenv()

    global OPENAI_API_KEY
    global PINECONE_API_KEY
    global PINECONE_ENVIRONMENT

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
