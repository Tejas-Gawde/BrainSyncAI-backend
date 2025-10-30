import os
from typing import Optional
from core.config import settings

from langchain_groq import ChatGroq
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_classic.agents import initialize_agent, AgentType


def run_search(query: str, api_key: Optional[str] = None) -> str:
    """
    Run the LLM-powered search agent on the given query and return the agent's response string.
    Raises RuntimeError if deps or API key missing.
    """

    prompt = f"""
    You are a concise web-search assistant.
    Answer the question below clearly using the tools available.
    If you find enough information, stop immediately.

    Question: {query}
    """


    # ✅ Prefer passed API key, else fallback to env or settings
    key = api_key or getattr(settings, "GROQ_API_KEY", None) or os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("Groq API key missing. Set GROQ_API_KEY or pass api_key parameter.")

    # Initialize wrappers and tools
    arxiv_wrapper = ArxivAPIWrapper(top_k_results=1, doc_content_chars_max=200)
    arxiv = ArxivQueryRun(api_wrapper=arxiv_wrapper)

    wiki_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=200)
    wiki = WikipediaQueryRun(api_wrapper=wiki_wrapper)

    search = DuckDuckGoSearchRun(name="Search")

    llm = ChatGroq(
        groq_api_key=key,
        model_name="Llama-3.1-8b-instant",
        streaming=False
    )

    tools = [search, arxiv, wiki]

    # ✅ Initialize agent (latest API)
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        handle_parsing_errors=True,
        verbose=True
    )

    # ✅ Run the query (must be a string)
    response = agent.run(prompt)

    return response
