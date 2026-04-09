import re
import yake
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.model_config import call_llm


# ---------- TEXT CLEAN ----------
def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


# ---------- EXTRACT UNIT NUMBER ----------
def extract_unit_number(name):
    if not name:
        return None

    match = re.search(r'unit\s*(\d+)', name.lower())

    if match:
        return int(match.group(1))

    return None


# ---------- EXTRACT TOPICS ----------
def extract_topics(text):

    kw = yake.KeywordExtractor(
        lan="en",
        n=2,
        dedupLim=0.7,
        top=12
    )

    topics = [k[0] for k in kw.extract_keywords(text)]

    return topics[:6]


# ---------- REMOVE SIMILAR ----------
def remove_similar_questions(qs):

    if len(qs) <= 1:
        return qs

    try:
        vec = TfidfVectorizer().fit_transform(qs)
        sim = cosine_similarity(vec)

        final = []

        for i in range(len(qs)):
            keep = True
            for j in range(len(final)):
                if sim[i][j] > 0.75:
                    keep = False
                    break
            if keep:
                final.append(qs[i])

        return final

    except:
        return qs


# ---------- LLM GENERATOR ----------
def llm_generate(unit_text, topics, difficulty, count):
    """
    Generate questions using the configured LLM model (dynamic).
    Automatically routes to Ollama (phi3:mini) or Gemini based on .env config.
    """
    if difficulty == "easy":
        style = "very short conceptual university exam questions"
        marks = 2
        length_rule = "Each question MUST be between 12 to 16 words only."

    elif difficulty == "medium":
        style = "moderate descriptive university exam questions"
        marks = 5
        length_rule = "Each question MUST be between 20 to 28 words only."

    else:
        style = "deep analytical long answer university exam questions"
        marks = 10
        length_rule = "Questions can be long between 40 to 70 words."

    topic_string = ", ".join(topics)

    prompt = f"""
You are an experienced university professor.

Generate {count} DIFFERENT academic exam questions.

Difficulty Level: {difficulty}
Question Style: {style}

IMPORTANT LENGTH RULE:
{length_rule}

Rules:
- Questions must be complete
- Avoid repetition
- Avoid copying lines from notes
- Cover MOST important concepts
- Maintain university exam tone
- Do NOT exceed the length rule

Topics:
{topic_string}

Notes:
{unit_text[:3500]}

Return only numbered questions.
"""

    try:
        # Use dynamic model configuration
        raw = call_llm(prompt, temperature=0.7)
    except Exception as e:
        print(f"❌ Error calling LLM: {e}")
        return [], marks

    qs = [
        q.strip("1234567890.- ").strip()
        for q in raw.split("\n")
        if len(q.strip()) > 12
    ]

    qs = remove_similar_questions(qs)

    return qs, marks


# ---------- MAIN ----------
def generate_questions(unit_notes_dict, difficulty="medium"):

    if difficulty == "easy":
        TOTAL_Q = 4
    elif difficulty == "hard":
        TOTAL_Q = 6
    else:
        TOTAL_Q = 5

    questions = []

    units = []

    for pdf_name, text in unit_notes_dict.items():

        unit_no = extract_unit_number(pdf_name)

        if unit_no is None:
            continue

        cleaned = clean_text(text)

        if len(cleaned) < 100:
            continue

        units.append((unit_no, cleaned))

    units = sorted(units, key=lambda x: x[0])

    if not units:
        return []

    unit_count = len(units)

    per_unit = max(1, TOTAL_Q // unit_count)

    for unit_no, text in units:

        topics = extract_topics(text)

        qs, marks = llm_generate(
            text,
            topics,
            difficulty,
            per_unit + 2
        )

        qs = qs[:per_unit]

        for q in qs:
            questions.append({
                "question": q,
                "marks": marks,
                "co": f"CO{unit_no}",
                "unit": f"Unit {unit_no}"
            })

    return questions[:TOTAL_Q]