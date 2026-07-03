from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def rank_resumes(job_description, resumes):
    documents = [job_description] + resumes

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(documents)

    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    ranked = sorted(
        list(enumerate(similarities)),
        key=lambda x: x[1],
        reverse=True
    )

    return ranked