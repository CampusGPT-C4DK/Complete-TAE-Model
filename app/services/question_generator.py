import re
from app.services.model_config import call_llm


def difficulty_logic(level):

    if level == "easy":
        return "conceptual short definition university questions", 2

    if level == "hard":
        return "analytical case-study numerical university questions", 10

    return "descriptive explanation university questions", 5


def ask_llm(unit_text, difficulty, count):
    """
    Generate questions using the configured LLM model (dynamic).
    Automatically routes to Ollama (phi3:mini) or Gemini based on .env config.
    """
    instruction, marks = difficulty_logic(difficulty)

    prompt = f"""
You are a senior university professor.

From the notes below generate {count} DIFFERENT {instruction}.

Rules:
- Questions must be complete
- Avoid copying text
- Avoid repeating verbs like Explain Explain Explain
- Cover different topics
- Questions must be exam ready

Notes:
{unit_text[:2500]}

Return only numbered questions.
"""

    try:
        # Use dynamic model configuration
        raw = call_llm(prompt, temperature=0.7)
    except Exception as e:
        print(f"❌ Error calling LLM: {e}")
        return [], marks

    questions = []

    for line in raw.split("\n"):
        line = re.sub(r"^\d+[\).\s]*", "", line).strip()
        if len(line) > 15:
            questions.append(line)

    return questions[:count], marks


def generate_questions(unit_notes, difficulty="medium"):

    final_questions = []

    per_unit_q = 2   # ⭐ 2 questions per unit → total depends on number of PDFs

    for i, (unit, text) in enumerate(unit_notes.items()):

        qs, marks = ask_llm(text, difficulty, per_unit_q)

        for q in qs:

            final_questions.append({
                "question": q,
                "marks": marks,
                "co": f"CO{i+1}",
                "unit": unit
            })

    return final_questions