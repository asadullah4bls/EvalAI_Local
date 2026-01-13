from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# =============================
# Load model ONCE
# =============================
saq_model = SentenceTransformer("all-MiniLM-L6-v2")
SAQ_THRESHOLD = 0.7


def evaluate_saq(user_answer, correct_answer):
    """
    Evaluate short-answer questions using semantic similarity
    """

    if not user_answer or not user_answer.strip():
        return {
            "is_correct": False,
            "similarity": 0.0
        }

    embeddings = saq_model.encode([user_answer, correct_answer])
    similarity = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]]
    )[0][0]

    return {
        "is_correct": similarity >= SAQ_THRESHOLD,
        "similarity": round(float(similarity), 2)
    }
