import requests
import json
from datetime import datetime
from config import *

# Conversation memory - keeps last N exchanges
_memory = []
MAX_MEMORY = 10  # remember last 10 exchanges


def _build_prompt(user_input: str) -> str:
    now = datetime.now().strftime("%A %d %B %Y, %H:%M")

    memory_block = ""
    if _memory:
        lines = []
        for entry in _memory[-MAX_MEMORY:]:
            lines.append(f"User: {entry['user']}")
            lines.append(f"Jarvis: {entry['jarvis']}")
        memory_block = "\n".join(lines)

    return f"""You are Jarvis, a smart desktop assistant running locally on Windows.

Current time: {now}

Personality:
- Casual, direct, a bit witty — like a clever mate who actually knows his stuff
- Short answers, 1-2 sentences unless the user asks for detail
- Never say you can't do something unless you genuinely can't
- No bullet points unless asked
- Don't repeat yourself or pad answers

Capabilities you have (handled by separate systems, don't explain how):
- Opening files and folders
- Controlling volume and brightness
- Web search
- Reading files
- Checking weather and time

{"Previous conversation:" + chr(10) + memory_block + chr(10) if memory_block else ""}
User: {user_input}
Jarvis:"""


def ask_ollama(prompt: str, remember: bool = True) -> str:
    try:
        full_prompt = _build_prompt(prompt)

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 150  # keep answers short
                }
            },
            timeout=120
        )

        data = response.json()

        if "response" not in data:
            print("Ollama error:", data.get("error", data))
            return "Something went wrong with Ollama."

        answer = data["response"].strip()

        # strip any "Jarvis:" prefix the model sometimes adds
        if answer.lower().startswith("jarvis:"):
            answer = answer[7:].strip()

        if remember:
            _memory.append({"user": prompt, "jarvis": answer})
            if len(_memory) > MAX_MEMORY:
                _memory.pop(0)

        print("\nJarvis:", answer)
        return answer

    except requests.exceptions.ConnectionError:
        return "Ollama isn't running. Go start it."
    except requests.exceptions.Timeout:
        return "Took too long. Try again."
    except Exception as e:
        print(f"ask_ollama error: {e}")
        return "Something went wrong."


def clear_memory():
    """Clear conversation history."""
    _memory.clear()
    print("Memory cleared.")


def get_memory_summary() -> str:
    if not _memory:
        return "No conversation history yet."
    return f"I remember {len(_memory)} exchanges from this session."