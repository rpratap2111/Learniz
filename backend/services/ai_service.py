import os
import requests
import json
import re
from dotenv import load_dotenv

# Load env variables
load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("HF_MODEL", "gpt2")
HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}


def call_hf(prompt: str, max_length: int = 256):
    """
    Calls Hugging Face Inference API with a prompt.
    Returns generated text or error message.
    """
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": max_length}}
    try:
        r = requests.post(HF_URL, headers=HEADERS, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()

        # Most models return [{"generated_text": "..."}]
        if isinstance(data, list) and isinstance(data[0], dict) and "generated_text" in data[0]:
            return data[0]["generated_text"]

        # Some models return dict
        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"]

        # Some return just string
        if isinstance(data, str):
            return data

        # Fallback: return raw JSON
        return json.dumps(data)

    except Exception as e:
        return f"Error calling HF API: {e}"


def generate_answer(query: str, subject: str) -> str:
    """
    Generate a concise and clear answer for a student's query.
    """
    prompt = (
        f"You are a helpful tutor for {subject}. "
        f"Answer the student's question concisely and clearly:\n\n"
        f"Question: {query}\n\nAnswer:"
    )
    return call_hf(prompt, max_length=200)


def generate_quiz(query: str, subject: str) -> dict:
    """
    Generate a related quiz (MCQ) in JSON format based on the student's query.
    Ensures 3 options and one correct answer.
    """
    prompt = (
        f"You are a quiz generator for {subject}. Based on the student question: \"{query}\", "
        "create ONE multiple-choice question (MCQ) that tests the same concept. "
        "Respond ONLY as JSON with keys: question (string), options (list of 3 strings), correct (one option).\n\n"
        "Example:\n"
        '{"question":"What does regex \\\\d match in Python?",'
        '"options":["Digits","Letters","Whitespace"],'
        '"correct":"Digits"}\n\n'
        "JSON:"
    )

    raw = call_hf(prompt, max_length=150)

    # Try to extract JSON from model output
    m = re.search(r"\{.*\}", raw, re.S)
    if m:
        try:
            j = json.loads(m.group(0).strip())

            # Ensure required fields
            if "question" in j and "options" in j and "correct" in j:
                # Fix options count if not 3
                if not isinstance(j["options"], list):
                    j["options"] = [str(j["options"])]
                if len(j["options"]) < 3:
                    while len(j["options"]) < 3:
                        j["options"].append("Extra Option")
                if len(j["options"]) > 3:
                    j["options"] = j["options"][:3]

                # Ensure correct is one of the options
                if j["correct"] not in j["options"]:
                    j["correct"] = j["options"][0]

                return j
        except Exception:
            pass

    # Fallback generic quiz
    return {
        "question": f"What concept is being tested related to: {query}?",
        "options": ["Option A", "Option B", "Option C"],
        "correct": "Option A",
    }
