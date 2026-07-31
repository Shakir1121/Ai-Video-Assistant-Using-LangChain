import os
import shutil
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Path for ChromaDB persistence
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")

# Load embedding model (FREE)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Text splitter for RAG - splits transcript into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    length_function=len,
    separators=["\n\n", "\n", ".", " ", ""]
)

db = None


def store_text(text: str):
    """Store text in ChromaDB for RAG-based retrieval using RecursiveCharacterTextSplitter."""
    global db

    # Guard: reject empty or very short text
    if not text or len(text.strip()) < 10:
        print("Warning: Text too short for ChromaDB storage, skipping.")
        return

    # Split text into chunks
    chunks = text_splitter.split_text(text)
    if not chunks or len(chunks) == 0:
        # If text splitting fails, use the whole text as one chunk
        chunks = [text]

    # Delete old ChromaDB to avoid stale/corrupted state
    if os.path.exists(CHROMA_DIR):
        try:
            shutil.rmtree(CHROMA_DIR)
        except Exception:
            pass

    # Create fresh ChromaDB (auto-persists in Chroma 0.4+)
    try:
        db = Chroma.from_texts(chunks, embeddings, persist_directory=CHROMA_DIR)
    except Exception as e:
        print(f"Warning: ChromaDB storage failed: {e}")
        db = None


def retrieve_text(query: str):
    """Retrieve relevant context from ChromaDB based on query."""
    global db
    if db is None:
        if os.path.exists(CHROMA_DIR):
            try:
                db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
            except Exception:
                return ""
        else:
            return ""
    try:
        docs = db.similarity_search(query, k=3)
        return " ".join([doc.page_content for doc in docs])
    except Exception:
        return ""
