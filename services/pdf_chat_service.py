from core.config import settings
import os
import tempfile
from datetime import datetime
from typing import Optional

from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

_STORE: dict = {}

def _now():
    return datetime.utcnow()

def _ensure_deps():
    if create_history_aware_retriever is None:
        raise RuntimeError("PDF chat dependencies are not installed. Install the required langchain packages.")

def _build_chain_from_pdf(path: str):
    """Builds a conversational RAG chain from a local PDF file path."""
    _ensure_deps()

    # embeddings
    hf_token = settings.HF_TOKEN
    groq_api_key = settings.GROQ_API_KEY
    if hf_token:
        os.environ["HF_TOKEN"] = hf_token
    if groq_api_key:
        os.environ["GROQ_API_KEY"] = groq_api_key
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # load and split
    loader = PyPDFLoader(path)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
    splits = text_splitter.split_documents(documents)

    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
    retriever = vectorstore.as_retriever()

    # prompts
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question which might reference context in the chat history, "
        "formulate a standalone question which can be understood without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    history_aware_retriever = create_history_aware_retriever(ChatGroq(model_name=settings.GROQ_MODEL_NAME), retriever, contextualize_q_prompt)

    system_prompt = (
        "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you don't know. Use three sentences maximum and keep the "
        "answer concise.\n\n{context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(ChatGroq(model_name=settings.GROQ_MODEL_NAME), qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    # session history manager
    def get_session_history(session: str) -> BaseChatMessageHistory:
        if session not in _STORE:
            _STORE[session] = ChatMessageHistory()
        return _STORE[session]

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    return conversational_rag_chain


def _write_temp_pdf(file_bytes: bytes, filename: Optional[str] = None) -> str:
    suffix = ".pdf"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(file_bytes)
    tmp.flush()
    tmp.close()
    return tmp.name


async def chat_with_pdf(file_bytes: bytes, question: str, session_id: Optional[str] = None) -> str:
    """
    Process uploaded PDF bytes and answer the provided question using RAG.
    Returns the assistant's answer string. Raises RuntimeError if deps missing.
    """
    _ensure_deps()
    tmp_path = _write_temp_pdf(file_bytes)
    try:
        chain = _build_chain_from_pdf(tmp_path)
        sid = session_id or "default_session"
        response = chain.invoke({"input": question}, config={"configurable": {"session_id": sid}})
        # response expected to be dict-like with 'answer'
        if isinstance(response, dict) and "answer" in response:
            return response["answer"]
        if isinstance(response, str):
            return response
        return str(response)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
