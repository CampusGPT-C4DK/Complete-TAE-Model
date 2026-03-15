import re
from collections import Counter


def extract_topics(text):

    sentences = re.split(r"[.?!]\s+", text)

    clean = []

    for s in sentences:
        s = s.strip()
        if len(s) > 40:
            clean.append(s)

    return clean


def keyword_score(sentences):

    words = []

    for s in sentences:
        tokens = re.findall(r"[A-Za-z]{4,}", s.lower())
        words.extend(tokens)

    freq = Counter(words)

    scored = []

    for s in sentences:

        tokens = re.findall(r"[A-Za-z]{4,}", s.lower())

        score = sum(freq[t] for t in tokens)

        scored.append((score, s))

    scored.sort(reverse=True)

    return [s for _, s in scored]


def build_topic_map(text):

    sentences = extract_topics(text)

    ranked = keyword_score(sentences)

    if len(ranked) < 6:
        return ranked

    step = len(ranked)//6

    topics = []

    for i in range(6):
        topics.append(ranked[i*step])

    return topics