import fitz  # PyMuPDF
import re

def extract_clean_text(pdf_path: str) -> str:
    """
    Extract and clean text from single or multi-page PDFs.
    Removes headers/footers, page numbers, TOC, references,
    front-page metadata, hyphen breaks, and noisy formatting.
    Preserves meaningful content.
    """

    # -----------------------------------------------------
    # 1. Extract text page-wise
    # -----------------------------------------------------
    doc = fitz.open(pdf_path)
    pages_text = [page.get_text("text") for page in doc]
    doc.close()

    full_text = "\n".join(pages_text)

    # Split lines
    lines = full_text.split("\n")

    # -----------------------------------------------------
    # 2. Detect + remove repeated headers/footers
    # -----------------------------------------------------
    freq = {}
    for line in lines:
        clean = line.strip()
        if len(clean) < 4:
            continue
        freq[clean] = freq.get(clean, 0) + 1

    cleaned_lines = [
        line for line in lines if freq.get(line.strip(), 0) < 3
    ]

    text = "\n".join(cleaned_lines)

    # -----------------------------------------------------
    # 3. Remove TOC (Table of Contents)
    # -----------------------------------------------------
    text = re.sub(
        r"(Table of Contents|Contents)(.|\n){0,500}", 
        "", 
        text, 
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # 4. Remove front-page sections (common in research PDFs)
    # -----------------------------------------------------
    front_page_patterns = [
        r"^abstract\b.*?(?=\n[A-Z])",
        r"^keywords\b.*?(?=\n[A-Z])",
        r"^author\b.*?(?=\n[A-Z])",
        r"^affiliation\b.*?(?=\n[A-Z])",
        r"^submitted.*?\n",
        r"^publication.*?\n",
    ]

    for pattern in front_page_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)

    # -----------------------------------------------------
    # 5. Remove References / Bibliography / Appendix sections
    # -----------------------------------------------------
    refs_patterns = [
        r"\nreferences\b(.|\n)*$",         # “References”
        r"\nbibliography\b(.|\n)*$",       # “Bibliography”
        r"\nworks cited\b(.|\n)*$",        # “Works Cited”
        r"\nappendix\b(.|\n)*$",           # “Appendix”
    ]

    for pattern in refs_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # -----------------------------------------------------
    # 6. Remove page numbers and page labels
    # -----------------------------------------------------
    # Standalone page numbers
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)

    # Page X or Page X of Y
    text = re.sub(r"Page\s*\d+(\s*of\s*\d+)?", "", text, flags=re.IGNORECASE)

    # -----------------------------------------------------
    # 7. Fix hyphenated line breaks
    # -----------------------------------------------------
    text = re.sub(r"-\s*\n\s*", "", text)

    # -----------------------------------------------------
    # 8. Merge broken lines inside paragraphs
    # -----------------------------------------------------
    text = re.sub(r"\n(?=[a-z])", " ", text)

    # -----------------------------------------------------
    # 9. Remove bullet symbols (keep your feature)
    # -----------------------------------------------------
    text = re.sub(r"[•▪●◦]", "", text)

    # -----------------------------------------------------
    # 10. Normalize special symbols (keep your feature)
    # -----------------------------------------------------
    text = (
        text.replace("–", "-")
            .replace("—", "-")
            .replace("“", '"')
            .replace("”", '"')
    )

    # -----------------------------------------------------
    # 11. Remove extra spaces/newlines (keep your feature)
    # -----------------------------------------------------
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"\s{2,}", " ", text)

    # -----------------------------------------------------
    # 12. Remove non-ASCII noise (keep your feature)
    # -----------------------------------------------------
    text = re.sub(r"[^\x00-\x7F]+", " ", text)

    return text.strip()


if __name__ == "__main__":
    test_pdf_path = r"C:\BLS\EvalAI5\Data_Sources\Urban_Traffic_Pattern_Clustering_And_Clustering_Image.pdf"  # Update with your PDF path
    cleaned_text = extract_clean_text(test_pdf_path)
    print("----- Cleaned Text Output -----\n")
    print(cleaned_text)