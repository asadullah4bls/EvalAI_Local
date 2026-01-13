# keyword_extractor/context.py
import sys
from keybert import KeyBERT

# --------------------------------------------------
# PATH SETUP
# --------------------------------------------------
cleaner_path = r"C:\BLS\EvalAI5\Text Cleaning"
text_cleaning_path = r"C:\BLS\EvalAI5\TextCleaning"
sys.path.append(cleaner_path)
sys.path.append(text_cleaning_path)

from   Text_Cleaning.textCleaner import extract_clean_text
from  Text_Cleaning.diagramText import extract_from_pdf

# --------------------------------------------------
# MODEL INITIALIZATION
# --------------------------------------------------
kw_model = KeyBERT()

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
TEXT_TOP_N = 30
DIAGRAM_TOP_N = 20

TEXT_MIN_SCORE = 0.50
DIAGRAM_MIN_SCORE = 0.25       # LOWER threshold (VERY IMPORTANT)
MIN_DIAGRAM_KEYWORDS = 5       # Force preservation

# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------
def extract_keywords_from_pdf(pdf_path):
    """
    Extract keywords from PDF text and diagrams separately
    to avoid dominance of a single topic.
    """

    # ===============================
    # STEP 1: CLEAN TEXT EXTRACTION
    # ===============================
    clean_text = extract_clean_text(pdf_path) or ""

    # ===============================
    # STEP 2: DIAGRAM OCR EXTRACTION
    # ===============================
    diagrams_list = extract_from_pdf(pdf_path)

    if isinstance(diagrams_list, list):
        diagrams_text = "\n".join(diagrams_list)
    else:
        diagrams_text = diagrams_list or ""

    final_keywords = {}

    # ===============================
    # STEP 3: TEXT KEYWORDS
    # ===============================
    if clean_text.strip():
        print("\n[✓] Extracting keywords from MAIN TEXT...")

        text_keywords = kw_model.extract_keywords(
            clean_text,
            keyphrase_ngram_range=(1, 3),
            stop_words="english",
            top_n=TEXT_TOP_N
        )

        for kw, score in text_keywords:
            if score >= TEXT_MIN_SCORE:
                final_keywords[kw] = {
                    "score": score,
                    "source": "text"
                }

    # ===============================
    # STEP 4: DIAGRAM KEYWORDS
    # ===============================
    diagram_kept = []

    if diagrams_text.strip():
        print("\n[✓] Extracting keywords from DIAGRAM TEXT...")

        diagram_keywords = kw_model.extract_keywords(
            diagrams_text,
            keyphrase_ngram_range=(1, 3),
            stop_words="english",
            top_n=DIAGRAM_TOP_N
        )

        for kw, score in diagram_keywords:
            if score >= DIAGRAM_MIN_SCORE:
                diagram_kept.append((kw, score))

        # 🔴 FORCE KEEP TOP DIAGRAM KEYWORDS
        if len(diagram_kept) < MIN_DIAGRAM_KEYWORDS:
            diagram_kept = diagram_keywords[:MIN_DIAGRAM_KEYWORDS]

        for kw, score in diagram_kept:
            if kw not in final_keywords or score > final_keywords[kw]["score"]:
                final_keywords[kw] = {
                    "score": score,
                    "source": "diagram"
                }

    # ===============================
    # STEP 5: SORT & FORMAT OUTPUT
    # ===============================
    merged_keywords = sorted(
        [(kw, meta["score"], meta["source"]) for kw, meta in final_keywords.items()],
        key=lambda x: x[1],
        reverse=True
    )

    # ===============================
    # STEP 6: LOG OUTPUT
    # ===============================
    print("\n══════════ FINAL KEYWORDS ══════════")
    for kw, score, source in merged_keywords:
        print(f"{kw} | {source} | score: {score:.4f}")

    print(f"\nTotal Keywords Extracted: {len(merged_keywords)}")
    print("════════════════════════════════════\n")

    return merged_keywords

# --------------------------------------------------
# TEST
# --------------------------------------------------
if __name__ == "__main__":
    test_pdf_path = r"C:\BLS\EvalAI5\Uploads\classification.pdf"
    extract_keywords_from_pdf(test_pdf_path)
