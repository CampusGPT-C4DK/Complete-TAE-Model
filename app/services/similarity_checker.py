from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def calculate_similarity(text1, text2):

    vectorizer = TfidfVectorizer()

    tfidf = vectorizer.fit_transform([text1, text2])

    similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])

    return round(float(similarity[0][0]) * 100, 2)