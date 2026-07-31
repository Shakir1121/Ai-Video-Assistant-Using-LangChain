import os
from langchain_mistralai import ChatMistralAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


llm = ChatMistralAI(
    model="mistral-large-latest",
    mistral_api_key=os.getenv("MISTRAL_API_KEY"),
    temperature=0.2,
    streaming=True
)

parser = StrOutputParser()


# =========================
# CHAIN BUILDERS (LangChain Runnables)
# =========================
def create_chain(system_prompt: str, human_prompt: str = "{input}"):
    """
    Build a LangChain Runnable chain: prompt | llm | StrOutputParser
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt),
    ])
    return prompt | llm | parser


def create_streaming_chain(system_prompt: str, human_prompt: str = "{input}"):
    """
    Build a LangChain Runnable chain with streaming: prompt | llm | StrOutputParser
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt),
    ])
    return prompt | llm | parser


# =========================
# STREAMING FUNCTION (backward-compatible)
# =========================
def stream_llm(prompt: str, system_prompt: str = "You are a helpful AI assistant."):
    chain = create_streaming_chain(system_prompt)
    for chunk in chain.stream({"input": prompt}):
        if chunk:
            yield chunk


# =========================
# NON-STREAM FUNCTION (backward-compatible)
# =========================
def generate_text(prompt: str, system_prompt: str = "You are a helpful AI assistant.") -> str:
    chain = create_chain(system_prompt)
    return chain.invoke({"input": prompt})
