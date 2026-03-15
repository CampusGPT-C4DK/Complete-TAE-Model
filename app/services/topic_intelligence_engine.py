import re
from sklearn.feature_extraction.text import TfidfVectorizer


def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text


def split_sentences(text):

    sentences = re.split(r"[.?!]\s+", text)

    clean = []

    for s in sentences:
        s = s.strip()
        if len(s) > 40:
            clean.append(s)

    return clean


def extract_top_topics(text, k=8):

    text = clean_text(text)

    sentences = split_sentences(text)

    if len(sentences) <= k:
        return sentences

    vec = TfidfVectorizer(stop_words="english")

    X = vec.fit_transform(sentences)

    scores = X.sum(axis=1)

    ranked = sorted(
        zip(scores.tolist(), sentences),
        reverse=True
    )

    topics = [s for _, s in ranked[:k]]

    return topics