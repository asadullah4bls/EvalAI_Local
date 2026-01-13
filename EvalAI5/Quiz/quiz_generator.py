# quiz_generator.py
import sys
import os
from groq import Groq
from dotenv import load_dotenv
import random
import textwrap

# ----------------------------
# Correct import path
# ----------------------------
#sys.path.append(r"C:\BLS\EvalAI5\Cluster")
from Cluster.cluster import cluster_keywords  # Must be directly inside /Cluster
from .saving_quiz  import parse_quiz, save_quiz, load_existing_quiz

# ----------------------------
# Load API Key
# ----------------------------
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
if API_KEY is None:
    raise ValueError("GROQ_API_KEY environment variable not set")

client = Groq(api_key=API_KEY)

# ============================================================
# Helper: Convert clusters dictionary → clean readable text
# ============================================================
def format_clusters_for_prompt(clusters: dict) -> str:
    """Convert clusters dictionary into readable bullet points."""
    formatted = ""
    for theme, keywords in clusters.items():
        formatted += f"\n{theme}:\n"
        for kw in keywords:
            formatted += f" - {kw}\n"
    return formatted.strip()

# ============================================================
# SAQ Generation
# ============================================================
def generate_saq(context_text, num_saq):
    saq_prompt = f"""
You are a highly skilled Quiz Generation expert. 
Your task is to generate up to {num_saq} Short Answer Questions (SAQs) based strictly on the
provided context.

CRITICAL RULES:
- You must not generate more than {num_saq} questions.
- Answers must be concise (1–2 lines), precise, and unambiguous.
- No blank answers.
- You are not bound to generate exact {num_saq} questions you can generate less questions if 
content is limited.
- Answers must be accurate.
- All questions must be logical.

CONTEXT:
{context_text}

OUTPUT FORMAT: Strictly follow this format:
Q1. <Question text>
Answer: <Correct answer> \n
Explanation: <Short explanation>
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": saq_prompt}],
        temperature=0.3,
        max_tokens=2000
    )
    return response.choices[0].message.content

# ============================================================
# MCQ Generation
# ============================================================
def generate_mcq(context_text, num_mcq):
    mcq_prompt = f"""
You are a highly skilled Quiz Generation expert. 
Your task is to generate up to {num_mcq} Multiple Choice Questions (MCQs) based strictly on 
the provided context.

CRITICAL RULES:
- You must not generate more than {num_mcq} questions.
- Each question must have exactly 4 options (A, B, C, D).
- Correct answer must be accurate.
- Include a 2–3 line concise explanation for the correct answer.
- You are not bound to generate exact {num_mcq} questions generate less questions if content
is limited.

CONTEXT:
{context_text}

OUTPUT FORMAT: Strictly follow this format:
Q1. <Question text>
   A) <Option A>
   B) <Option B>
   C) <Option C>
   D) <Option D>
Correct Answer: <A/B/C/D>
Explanation: <Concise explanation>
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": mcq_prompt}],
        temperature=0.3,
        max_tokens=2000
    )
    return response.choices[0].message.content

# ============================================================
# Clean & Validate Parsed Questions
# ============================================================
def clean_parsed_questions(questions):
    """Remove empty/untitled questions, invalid MCQs, duplicate questions, and clean 
    explanations."""
    cleaned = []
    banned_phrases = [
        "based on the provided context",
        "i will generate",
        "following questions",
        "here are"
    ]

    for q in questions:
        question_text = q.get("question", "").strip()
        if not question_text:
            continue
        if any(bp in question_text.lower() for bp in banned_phrases):
            continue

        # MCQ validation
        if q.get("type") == "MCQ":
            options = q.get("options", {})
            if len(options) < 4 or any(not str(opt).strip() for opt in options.values()):
                continue
            if not q.get("correct_answer"):
                continue
        # SAQ validation
        else:
            if not q.get("answer"):
                continue

        # Clean explanation
        if "explanation" in q and q["explanation"]:
            q["explanation"] = " ".join(q["explanation"].split())

        cleaned.append(q)

    # Deduplicate questions by normalized text
    seen = set()
    final_cleaned = []
    for q in cleaned:
        key = q['question'].strip().lower()
        if key not in seen:
            final_cleaned.append(q)
            seen.add(key)

    return final_cleaned

# ============================================================
# Generate Full Quiz from Clusters
# ============================================================
def generate_quiz_from_clusters(context_text, max_questions):
    num_saq = max(1, int(max_questions * 0.7))
    num_mcq = max_questions - num_saq

    saq_text = generate_saq(context_text, num_saq)
    mcq_text = generate_mcq(context_text, num_mcq)

    # Parse questions
    saq_parsed = parse_quiz(saq_text)         # SAQs
    mcq_parsed = parse_quiz(mcq_text)     # MCQs (fixed)

    # Tag types
    for q in saq_parsed:
        q["type"] = "SAQ"
    for q in mcq_parsed:
        q["type"] = "MCQ"

    # Clean and deduplicate
    saq_parsed = clean_parsed_questions(saq_parsed)
    mcq_parsed = clean_parsed_questions(mcq_parsed)

    # Combine and shuffle
    full_quiz = saq_parsed + mcq_parsed
    random.shuffle(full_quiz)

    return full_quiz

# ============================================================
# Full PDF → Quiz Pipeline
# ============================================================
def generate_quiz_from_pdf(pdf_path, max_questions=20, save=True):
    existing = load_existing_quiz(pdf_path)
    if existing:
        return existing

    clusters = cluster_keywords(pdf_path)
    clean_context = format_clusters_for_prompt(clusters)

    quiz_list = generate_quiz_from_clusters(clean_context, max_questions)

    if save:
        save_quiz(pdf_path, quiz_list)

    return {
        "pdf_path": pdf_path,
        "quiz": quiz_list
    }

# ============================================================
# Pretty Print Quiz
# ============================================================
def display_quiz_pretty(quiz):
    print("\n==================== QUIZ ====================\n")
    wrap_width = 100
    for idx, q in enumerate(quiz["quiz"], start=1):
        print(f"Q{idx}. {q['question']}")
        if 'options' in q:
            for opt in ["A","B","C","D"]:
                print(f"   {opt}) {textwrap.fill(q['options'][opt], wrap_width, subsequent_indent='      ')}")
            print(f"Correct Answer: {q['correct_answer']}")
        else:
            print(f"Answer: {textwrap.fill(q['answer'], wrap_width, subsequent_indent='   ')}")
        if 'explanation' in q:
            print(f"Explanation: {textwrap.fill(q['explanation'], wrap_width, subsequent_indent='   ')}")
        print("\n---------------------------------------------\n")

# ============================================================
# Test Entry Point
# ============================================================
if __name__ == "__main__":
    test_pdf = r"C:\BLS\EvalAI5\Uploads\Transformer_attention_3.pdf"  # Update if needed
    max_questions = 20
    quiz_data = generate_quiz_from_pdf(test_pdf, max_questions, save=True)
    display_quiz_pretty(quiz_data)
