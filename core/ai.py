import requests

from config import *

def ask_ollama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": f"""You are Jarvis, an engineering assistant.

IMPORTANT:
- You do NOT have direct access to files.
- You do NOT claim to have found, opened, scanned, reviewed, or analyzed files.
- File searching is handled by a separate system.
- Never invent file search results.

Rules:
- Keep answers short.
- Maximum 2 sentences.
- Focus on engineering, Arduino, electronics, programming, university projects and SolidWorks.
- No bullet points unless asked.
- Be direct.

User: {prompt}""",
            "stream": False
        },
        timeout=120
    )

    answer = response.json()["response"].strip()

    print("\nJarvis:", answer)

    return answer
