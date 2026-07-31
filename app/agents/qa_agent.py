from app.tools.llm_loader import create_streaming_chain
from app.memory.vector_store import retrieve_text

SYSTEM_PROMPT = """You are an expert AI assistant answering questions about a video transcript.

I will provide you with:
1. The user's question
2. The MOST RELEVANT parts of the transcript retrieved from ChromaDB vector search (not the full transcript)

Rules:
- Answer the question using ONLY the retrieved transcript context provided
- If the context doesn't contain enough information to answer, say "The video transcript doesn't contain information about this."
- Do NOT make up information or use outside knowledge about the video
- Fix obvious transcription errors (e.g., "credit" for "CRUD")
- Be accurate, clear, and concise"""

chain = create_streaming_chain(SYSTEM_PROMPT, human_prompt="{input}")


def qa_agent_stream(transcript: str = None, question: str = None):
    """
    Answer questions using RAG - retrieves only relevant chunks from ChromaDB
    instead of sending the full transcript to the LLM.
    
    Args:
        transcript: Kept for backward compatibility but IGNORED (uses vector store instead)
        question: The user's question
    """
    if not question:
        return

    # Use ChromaDB RAG: retrieve only the most relevant chunks for the question
    retrieved_context = retrieve_text(question)

    if not retrieved_context or len(retrieved_context.strip()) < 10:
        # Fallback: if nothing was retrieved from ChromaDB, use the full transcript
        if transcript:
            full_input = f"Question: {question}\n\nTranscript context: {transcript}\n\nAnswer clearly:"
        else:
            yield "No transcript data found in the vector store. Please process a video first."
            return
    else:
        # RAG path: only send the retrieved chunks (much smaller, more relevant)
        full_input = f"Question: {question}\n\nRelevant transcript context from video:\n{retrieved_context}\n\nAnswer clearly based on the above context:"

    for chunk in chain.stream({"input": full_input}):
        if chunk:
            yield chunk
