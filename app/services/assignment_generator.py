import ollama
import re
import yake
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------- TEXT CLEAN ----------
def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


# ---------- EXTRACT UNIT NUMBER FROM PDF NAME ----------
def extract_unit_number(name):

    if not name:
        return None

    match = re.search(r'unit\s*(\d+)', name.lower())

    if match:
        return int(match.group(1))

    return None


# ---------- EXTRACT IMPORTANT TOPICS ----------
def extract_topics(text):

    kw = yake.KeywordExtractor(
        lan="en",
        n=2,
        dedupLim=0.7,
        top=12
    )

    topics = [k[0] for k in kw.extract_keywords(text)]

    return topics[:6]


# ---------- REMOVE SIMILAR QUESTIONS ----------
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


# ---------- LLM QUESTION GENERATION ----------
def llm_generate(unit_text, topics, difficulty, count):

    if difficulty == "easy":
        style = "short conceptual university exam questions"
        marks = 2

    elif difficulty == "hard":
        style = "deep analytical long answer university exam questions"
        marks = 10

    else:
        style = "descriptive medium level university exam questions"
        marks = 5

    topic_string = ", ".join(topics)

    prompt = f"""
You are an experienced university professor.

Generate {count} DIFFERENT academic exam questions.

Difficulty Level: {difficulty}
Question Style: {style}

Rules:
- Questions must be complete
- Avoid repetition
- Avoid copying lines from notes
- Cover the MOST important concepts
- Use verbs like analyse, justify, compare, derive, evaluate
- Maintain university exam tone

Topics:
{topic_string}

Notes:
{unit_text[:3500]}

Return only numbered questions.
"""

    response = ollama.chat(
        model="phi3",
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response["message"]["content"]

    qs = [
        q.strip("1234567890.- ").strip()
        for q in raw.split("\n")
        if len(q.strip()) > 12
    ]

    qs = remove_similar_questions(qs)

    return qs, marks


# ---------- MAIN GENERATOR ----------
def generate_questions(unit_notes_dict, difficulty="medium"):

    if not isinstance(unit_notes_dict, dict):
        return []

    if difficulty == "easy":
        TOTAL_Q = 4
    elif difficulty == "hard":
        TOTAL_Q = 6
    else:
        TOTAL_Q = 5

    questions = []

    units = []

    # ---------- BUILD UNIT STRUCTURE ----------
    for pdf_name, text in unit_notes_dict.items():

        unit_no = extract_unit_number(pdf_name)

        if unit_no is None:
            continue

        cleaned = clean_text(text)

        if len(cleaned) < 100:
            continue

        units.append((unit_no, cleaned))

    # ---------- SORT BY ACTUAL UNIT NUMBER ----------
    units = sorted(units, key=lambda x: x[0])

    if not units:
        return []

    unit_count = len(units)

    per_unit = max(1, TOTAL_Q // unit_count)

    # ---------- GENERATE QUESTIONS ----------
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