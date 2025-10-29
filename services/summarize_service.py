from typing import Optional
from core.config import settings

try:
    import validators
    from langchain_core.documents import Document
    from langchain_core.prompts import PromptTemplate
    from langchain_groq import ChatGroq
    from langchain_classic.chains import load_summarize_chain
    from langchain_community.document_loaders import YoutubeLoader, UnstructuredURLLoader
except Exception as e:
    # If imports fail, we'll raise at runtime with a clear error message
    validators = None  # type: ignore


PROMPT_TEMPLATE = """
Summarize the content below using well-structured Markdown. Include:
- Title
- TL;DR (2-3 sentences)
- Key Points (bulleted)
- Summary (150-250 words)
- Notable Quotes (optional)
- Topics/Tags (comma-separated)

Content:
{text}

Return only Markdown.
"""


def _ensure_deps():
    if validators is None:
        raise RuntimeError("Required summarization libraries are not installed (langchain, langchain_groq, validators).")

def _truncate(text: str, max_chars: int = 12000) -> str:
    return text if len(text) <= max_chars else text[:max_chars]

def _build_prompt():
    return PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["text"])  # type: ignore

async def summarize_youtube(url: str) -> str:
    """
    Attempt to summarize the provided YouTube URL using the same logic as the standalone script.
    Raises RuntimeError if required libs or API key are missing.
    Returns the generated markdown summary as a string.
    """
    _ensure_deps()

    if not validators.url(url):
        raise ValueError("Invalid URL")

    api_key = settings.GROQ_API_KEY
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set in environment")

    # Initialize LLM
    llm = ChatGroq(model=settings.GROQ_MODEL_NAME, groq_api_key=api_key)

    # Load content
    if "youtube.com" in url or "youtu.be" in url:
        preferred_langs = ["en", "en-US", "en-GB"]
        loader = YoutubeLoader.from_youtube_url(url, add_video_info=False, language=preferred_langs, translation=None)
        docs = loader.load()
    else:
        loader = UnstructuredURLLoader(urls=[url], ssl_verify=False)
        docs = loader.load()

    if not docs:
        raise RuntimeError("No content could be extracted from the provided URL")

    combined_text = "\n\n".join([getattr(d, "page_content", "") for d in docs]).strip()
    combined_text = _truncate(combined_text)

    chain = load_summarize_chain(llm, chain_type="stuff", prompt=_build_prompt())
    single_doc = Document(page_content=combined_text, metadata={})
    out = chain.invoke({"input_documents": [single_doc]})

    # chain.invoke can return a string or dict depending on chain implementation
    if isinstance(out, dict) and "output_text" in out:
        return out["output_text"]
    if isinstance(out, str):
        return out
    return str(out)
