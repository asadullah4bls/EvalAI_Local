from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
import numpy as np

# ----------------------------------
# NLTK SETUP
# ----------------------------------
nltk.download("stopwords")
STOPWORDS = set(stopwords.words("english"))

# ----------------------------------
# IMPORT KEYWORD EXTRACTOR
# ----------------------------------
from .keywords_text  import extract_keywords_from_pdf

# ----------------------------------
# EMBEDDING MODEL
# ----------------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# ----------------------------------
# CONFIG
# ----------------------------------
TEXT_SIM_THRESHOLD = 0.65
DIAGRAM_SIM_THRESHOLD = 0.75   # Less aggressive pruning
MIN_DIAGRAM_KEYWORDS = 5


def get_filtered_keywords_from_pdf(pdf_path):
    """
    Extract source-aware keywords and apply intelligent filtering.
    """
    raw_keywords = extract_keywords_from_pdf(pdf_path)

    if not raw_keywords:
        return []

    # Split by source
    text_keywords = []
    diagram_keywords = []

    for kw, score, source in raw_keywords:
        if source == "diagram":
            diagram_keywords.append((kw, score))
        else:
            text_keywords.append((kw, score))

    # Filter independently
    filtered_text = filter_by_similarity(
        text_keywords, threshold=TEXT_SIM_THRESHOLD
    )

    filtered_diagram = filter_by_similarity(
        diagram_keywords, threshold=DIAGRAM_SIM_THRESHOLD
    )

    # 🔴 Force diagram preservation
    if len(filtered_diagram) < MIN_DIAGRAM_KEYWORDS:
        filtered_diagram = [kw for kw, _ in diagram_keywords[:MIN_DIAGRAM_KEYWORDS]]

    # Final merge
    final_keywords = filtered_text + filtered_diagram
    return final_keywords


def filter_by_similarity(keywords, threshold):
    """
    Remove stopwords, duplicates, and semantically similar keywords.
    """
    if not keywords:
        return []

    # ----------------------------------
    # CLEAN TEXT
    # ----------------------------------
    cleaned = []
    for kw, _ in keywords:
        words = kw.split()
        filtered_words = [w for w in words if w.lower() not in STOPWORDS]
        if filtered_words:
            cleaned.append(" ".join(filtered_words).lower())

    if not cleaned:
        return []

    # Remove exact duplicates
    cleaned = list(dict.fromkeys(cleaned))

    # ----------------------------------
    # EMBEDDING SIMILARITY
    # ----------------------------------
    embeddings = model.encode(cleaned)
    similarity_matrix = cosine_similarity(embeddings)

    kept = []
    kept_indices = []

    for i, kw in enumerate(cleaned):
        if not kept:
            kept.append(kw)
            kept_indices.append(i)
            continue

        sims = [similarity_matrix[i][j] for j in kept_indices]
        if all(sim < threshold for sim in sims):
            kept.append(kw)
            kept_indices.append(i)

    return kept


# ----------------------------------
# TEST
# ----------------------------------
if __name__ == "__main__":
    pdf_path = r"C:\BLS\EvalAI5\Uploads\classification.pdf"

    final_keywords = get_filtered_keywords_from_pdf(pdf_path)

    print("\n=== FINAL FILTERED KEYWORDS ===")
    for kw in final_keywords:
        print(kw)

    print(f"\nTotal Keywords after filtering: {len(final_keywords)}")
