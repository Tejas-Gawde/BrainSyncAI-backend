import os
from typing import Optional
from core.config import settings

try:
    from langchain_groq import ChatGroq
    from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
    from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun, DuckDuckGoSearchRun
    from langchain_classic.agents import initialize_agent, AgentType
except Exception:
    ChatGroq = None  # type: ignore


def _ensure_deps():
    if ChatGroq is None:
        raise RuntimeError("LLM search dependencies are not installed. Install langchain and related packages.")



def run_search(query: str, api_key: Optional[str] = None) -> str:
    """
    Run the LLM-powered search agent on the given query and return the agent's response string.
    Raises RuntimeError if deps or API key missing.
    """
    _ensure_deps()

    key = settings.GROQ_API_KEY 
    if not key:
        raise RuntimeError("GROQ_API_KEY not set in environment")

    # initialize wrappers and tools
    arxiv_wrapper = ArxivAPIWrapper(top_k_results=1, doc_content_chars_max=200)
    arxiv = ArxivQueryRun(api_wrapper=arxiv_wrapper)

    wiki_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=200)
    wiki = WikipediaQueryRun(api_wrapper=wiki_wrapper)

    search = DuckDuckGoSearchRun(name="Search")

    llm = ChatGroq(groq_api_key=key, model_name="Llama-3.1-8b-instant", streaming=False)
    tools = [search, arxiv, wiki]

    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        handle_parsing_errors=True,
        max_iterations=10,
        max_execution_time=120,
    )

    # run the agent on the query
    out = agent.run(query)
    return out
