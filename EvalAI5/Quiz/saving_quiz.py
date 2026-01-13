# saving_quiz.py
import os
import re
import json
import hashlib
import datetime
# ----------------------------
# Ensure quizzes folder exists
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUIZZES_FOLDER = os.path.join(BASE_DIR, "../Quiz/quizzes")
USER_ATTEMPTS_FOLDER =  os.path.join(BASE_DIR, "../Quiz/user_quizzes")

def parse_quiz(raw_text):
    """
    Converts LLM text output into a structured list of quiz items (MCQs and SAQs).
    Ensures explanations are separate from options in MCQs.
    """
    parts = re.split(r'\n?Q\d+\.\s*', raw_text)
    parts = [p.strip() for p in parts if p.strip()]

    quiz_items = []

    for part in parts:
        try:
            # Check if this is an MCQ (look for options A-D)
            # Stop option capturing at "Explanation:"
            option_matches = re.findall(
                r'([A-D])\)\s*(.*?)(?=\s*[A-D]\)|\s*Correct Answer:|\s*Explanation:|$)',
                part,
                re.DOTALL
            )

            if option_matches:
                # It's an MCQ
                question_match = re.match(r'(.+?)\s*A\)', part, re.DOTALL)
                question_text = question_match.group(1).strip() if question_match else "Untitled Question"

                # Extract options
                options = {key: value.strip().replace("\n", " ") for key, value in option_matches}

                # Extract correct answer
                correct_match = re.search(r'Correct Answer:\s*([A-D])', part)
                correct_answer = correct_match.group(1).strip() if correct_match else ""

                # Extract explanation (everything after 'Explanation:')
                explanation_match = re.search(r'Explanation:\s*(.+)', part, re.DOTALL)
                explanation = explanation_match.group(1).strip() if explanation_match else ""
                explanation = " ".join(explanation.split())

                quiz_items.append({
                    "question": question_text,
                    "options": options,
                    "correct_answer": correct_answer,
                    "explanation": explanation,
                    "type": "MCQ"
                })
            else:
                # It's a SAQ
                question_match = re.match(r'(.+?)\s*Answer:', part, re.DOTALL)
                question_text = question_match.group(1).strip() if question_match else part.split("Answer:")[0].strip()

                # Extract answer (everything after 'Answer:' but before 'Explanation:' if present)
                answer_match = re.search(r'Answer:\s*(.+?)(?:Explanation:|$)', part, re.DOTALL)
                answer_text = answer_match.group(1).strip() if answer_match else ""

                # Optional explanation for SAQ
                explanation_match = re.search(r'Explanation:\s*(.+)', part, re.DOTALL)
                explanation = explanation_match.group(1).strip() if explanation_match else ""

                quiz_items.append({
                    "question": question_text,
                    "answer": answer_text,
                    "explanation": " ".join(explanation.split()) if explanation else "",
                    "type": "SAQ"
                })

        except Exception as e:
            print(f"⚠️ Error parsing quiz item: {e}")

    return quiz_items

# ============================================================
# Save or retrieve quiz from cache
# ============================================================
def save_quiz(pdf_path, raw_quiz_text):
    """
    Parses LLM output and saves the quiz in structured JSON format.
    Supports:
    - Single PDF
    - Multiple PDFs (combined into ONE quiz file)
    """
    os.makedirs(USER_ATTEMPTS_FOLDER, exist_ok=True)
    os.makedirs(QUIZZES_FOLDER, exist_ok=True)
    if isinstance(pdf_path, list):
        base_names = [
            os.path.splitext(os.path.basename(p))[0]
            .replace(" ", "_")
            .replace("-", "_")
            for p in pdf_path
        ]

        combined_name = "_".join(base_names)
        quiz_file_path = os.path.join(QUIZZES_FOLDER, f"{combined_name}.json")

        combined_string = "|".join(sorted(pdf_path))
        pdf_hash = hashlib.sha256(combined_string.encode("utf-8")).hexdigest()

    # ----------------------------
    # SINGLE PDF (UNCHANGED)
    # ----------------------------
    else:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        base_name = base_name.replace(" ", "_").replace("-", "_")
        quiz_file_path = os.path.join(QUIZZES_FOLDER, f"{base_name}.json")
        pdf_hash = hashlib.sha256(pdf_path.encode("utf-8")).hexdigest()

    # ----------------------------
    # CACHE CHECK
    # ----------------------------
    if os.path.exists(quiz_file_path):
        print(f"\n⚠️ Quiz already exists: {quiz_file_path}")
        return quiz_file_path

    # ----------------------------
    # Parse only if raw text (LLM output)
    # ---------------------------------
    if isinstance(raw_quiz_text, str):
        structured_quiz = parse_quiz(raw_quiz_text)
        if not structured_quiz:
            raise ValueError("Parsed quiz is empty. No valid questions generated.")
    elif isinstance(raw_quiz_text, list):
        structured_quiz = raw_quiz_text
    else:
        raise ValueError("Unsupported quiz format passed to save_quiz")


    data = {
        "pdf_path": pdf_path,
        "pdf_hash": pdf_hash,
        "quiz": structured_quiz,
        "created_at": str(datetime.datetime.now())
    }

    # ----------------------------
    # SAVE JSON
    # ----------------------------
    with open(quiz_file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"\n✅ Quiz saved: {quiz_file_path}")
    return quiz_file_path

def save_user_attempt(user_id, pdf_names, attempt_record):
    """
    Saves a user's quiz attempt.
    MCQs are already evaluated.
    SAQs are stored for later evaluation.
    """

    # ----------------------------
    # Safe filename (NO UUID)
    # ----------------------------
    safe_pdf_part = "_".join(
        [os.path.splitext(name)[0].replace(" ", "_") for name in pdf_names]
    )

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{user_id}_{safe_pdf_part}_{timestamp}.json"
    filepath = os.path.join(USER_ATTEMPTS_FOLDER, filename)

    # ----------------------------
    # Save attempt
    # ----------------------------
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(
            {
                "user_id": user_id,
                "pdf_names": pdf_names,
                "attempted_at": timestamp,

                # MCQ evaluation (already done)
                "mcq_score": attempt_record.get("mcq_score"),
                "mcq_total": attempt_record.get("mcq_total"),
                "mcq_details": attempt_record.get("mcq_details"),

                # SAQ (pending)
                "saq_answers": attempt_record.get("saq_answers"),
                "saq_status": attempt_record.get("saq_status", "pending"),
            },
            f,
            indent=4,
            ensure_ascii=False,
        )

    return {
        "status": "success",
        "file_saved": filename,
        "mcq_score": attempt_record.get("mcq_score"),
        "mcq_total": attempt_record.get("mcq_total"),
        "saq_pending": len(attempt_record.get("saq_answers", {})),
    }

def load_existing_quiz(pdf_paths):
    """
    pdf_paths: str OR list[str]
    """

    # ----------------------------
    # Normalize input
    # ----------------------------
    if isinstance(pdf_paths, str):
        pdf_paths = [pdf_paths]

    if not pdf_paths:
        return None

    # ----------------------------
    # SINGLE PDF (keep existing behavior)
    # ----------------------------
    if len(pdf_paths) == 1:
        base_name = os.path.splitext(os.path.basename(pdf_paths[0]))[0]
        quiz_file_path = os.path.join(QUIZZES_FOLDER, f"{base_name}.json")

        if os.path.exists(quiz_file_path):
            print(f"\n📥 Loaded existing quiz: {quiz_file_path}\n")
            with open(quiz_file_path, "r", encoding="utf-8") as f:
                return json.load(f)

        return None

    # ----------------------------
    # MULTIPLE PDFs (merged filename)
    # ----------------------------
    base_names = [
        os.path.splitext(os.path.basename(p))[0]
        for p in pdf_paths
    ]

    combined_name = "_".join(base_names)
    quiz_file_path = os.path.join(QUIZZES_FOLDER, f"{combined_name}.json")

    if os.path.exists(quiz_file_path):
        print(f"\n📥 Loaded existing merged quiz: {quiz_file_path}\n")
        with open(quiz_file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return None
