import json
import urllib.request
import urllib.error


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "gemma3:4b"


def generate_answer(
    question: str,
    context: str,
) -> str:

    prompt = f"""
You are the AI assistant for an Enterprise Knowledge Intelligence Platform.

Your job is to answer the user's question using ONLY the enterprise
knowledge provided below.

STRICT RULES:

1. Use only information contained in the enterprise knowledge.
2. Never use outside knowledge.
3. Never invent facts, numbers, dates, names, policies, or procedures.
4. Give the direct answer first.
5. Always answer in a complete, natural sentence.
6. If the question asks for a number, include the number AND what the
   number refers to.
7. Keep the answer short: normally one or two sentences.
8. Do not copy large sections of the source document.
9. Do not mention embeddings, retrieval, vectors, similarity scores,
   confidence scores, or internal system details.
10. If the enterprise knowledge does not contain enough information to
    answer the question, say exactly:

"I couldn't find that information in the approved enterprise knowledge base."

EXAMPLES:

Question:
How many days of casual leave are employees entitled to?

Good answer:
Employees are entitled to 15 days of Casual Leave per calendar year.

Bad answer:
15 Days

Question:
How many days of sick leave are employees entitled to?

Good answer:
Employees are entitled to 10 days of Sick Leave per calendar year.

Bad answer:
10 Days

Question:
What is the carry-forward limit for sick leave?

Good answer:
Employees can carry forward up to 5 days of Sick Leave.

Bad answer:
5 Days

ENTERPRISE KNOWLEDGE:
{context}

USER QUESTION:
{question}

ANSWER:
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 100,
        },
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=120,
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

        answer = (
            result.get("response")
            or ""
        ).strip()

            # -----------------------------------------------------
        # Normalize very short numeric answers
        # -----------------------------------------------------

        import re

        if (
            len(answer.split()) <= 4
            and re.fullmatch(
                r"\d+\s*(day|days|month|months|year|years)",
                answer,
                re.IGNORECASE,
            )
        ):

            lower_question = question.lower()

            # Casual Leave
            if "casual leave" in lower_question:
                answer = (
                    f"Employees are entitled to {answer} "
                    "of Casual Leave per calendar year."
                )

            # Sick Leave
            elif "sick leave" in lower_question:
                answer = (
                    f"Employees are entitled to {answer} "
                    "of Sick Leave per calendar year."
                )

            # Earned / Privilege Leave
            elif (
                "earned leave" in lower_question
                or "privilege leave" in lower_question
            ):
                answer = (
                    f"Employees are entitled to {answer} "
                    "of Earned / Privilege Leave per calendar year."
                )

        if not answer:
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        return answer

    except urllib.error.URLError as exc:

        raise RuntimeError(
            "Could not connect to local Ollama. "
            "Make sure Ollama is running."
        ) from exc

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            "Ollama returned an invalid response."
        ) from exc