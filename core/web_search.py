import requests
import re
from config import *


def web_search(query: str, num_results: int = 3) -> str:
    """
    Search DuckDuckGo and return a brief summary.
    No API key needed.
    """
    try:
        # DuckDuckGo instant answer API
        r = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            },
            timeout=8,
            headers={"User-Agent": "Jarvis/1.0"}
        )
        data = r.json()

        # Try instant answer first
        abstract = data.get("AbstractText", "").strip()
        if abstract:
            source = data.get("AbstractSource", "")
            short = _truncate(abstract, 200)
            return f"{short} (Source: {source})" if source else short

        # Try answer (e.g. calculations, conversions)
        answer = data.get("Answer", "").strip()
        if answer:
            return answer

        # Try related topics
        topics = data.get("RelatedTopics", [])
        snippets = []
        for t in topics[:num_results]:
            if isinstance(t, dict) and t.get("Text"):
                snippets.append(_truncate(t["Text"], 100))

        if snippets:
            return " | ".join(snippets)

        # Fallback — tell Ollama to answer from its own knowledge
        return None

    except Exception as e:
        print(f"Web search error: {e}")
        return None


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "..."


def handle_web_search(text: str, ask_ollama_fn) -> str:
    """
    Detect search intent, run search, feed result to Ollama for a natural answer.
    Returns response string or None if no search intent.
    """
    t = text.lower().strip()

    # Explicit search triggers
    search_triggers = [
        "search for", "look up", "google", "find out", "search",
        "what is", "who is", "who was", "when did", "when was",
        "how does", "how do", "why does", "why did",
        "latest", "recent", "news about", "tell me about",
        "define", "definition of", "meaning of",
    ]

    is_search = any(t.startswith(trigger) or f" {trigger} " in t for trigger in search_triggers)

    # Also search if it ends with a question mark
    if text.strip().endswith("?"):
        is_search = True

    if not is_search:
        return None

    # Clean up the query
    query = text
    for prefix in ["search for", "look up", "google", "search", "find out about", "find out"]:
        if t.startswith(prefix):
            query = text[len(prefix):].strip()
            break

    print(f"Searching: {query}")
    result = web_search(query)

    if result:
        # Feed search result to Ollama for a natural spoken answer
        prompt = f"""The user asked: "{text}"

Web search result: {result}

Answer the user's question naturally in 1-2 sentences based on the search result. Be direct."""
        return ask_ollama_fn(prompt, remember=False)
    else:
        # Let Ollama answer from its own knowledge
        return None