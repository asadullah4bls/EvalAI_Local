from flask import Flask,render_template,  request, jsonify
from flask_cors import CORS
import os
import sys
import random
import uuid
from  Quiz.quiz_generator   import    generate_quiz_from_pdf
from   Quiz.saving_quiz   import   save_quiz, save_user_attempt, load_existing_quiz
import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # This does NOT actually connect to the internet
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# ----------------------------
# Project imports
# ----------------------------
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Quiz')))
# sys.path.append(r"C:\BLS\EvalAI5\Quiz") 
# from qa_evaluator import evaluate_saq

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER =  os.path.join(BASE_DIR, "../Uploads")
# UPLOAD_FOLDER = r"C:\BLS\EvalAI5\Uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
MAX_QUESTIONS = 20

@app.route("/")
def upload_page():
    return render_template("upload.html")

@app.route("/quiz")
def quiz_page():
    return render_template("quiz.html")

@app.route("/result")
def result_page():
    return render_template("result.html")


# ======================================================
# 1️⃣ UPLOAD PDFs & GENERATE QUIZ
# ======================================================
@app.route("/upload_pdfs/", methods=["POST"])
def upload_pdfs():
    if "files" not in request.files:
        return jsonify({"error": "No files part in request"}), 400
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400
    pdf_paths = []
    for file in files:
        pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(pdf_path)
        pdf_paths.append(pdf_path)
    per_pdf_quizzes = {}

    # Generate quiz per PDF
    for path in pdf_paths:
        quiz_data = generate_quiz_from_pdf(
            pdf_path=path,
            max_questions=MAX_QUESTIONS,
            save=False
        )
        per_pdf_quizzes[path] = quiz_data["quiz"]

    # Trim fairly if exceeding max
    total_questions = sum(len(q) for q in per_pdf_quizzes.values())

    while total_questions > MAX_QUESTIONS:
        largest_pdf = max(per_pdf_quizzes, key=lambda k: len(per_pdf_quizzes[k]))
        if len(per_pdf_quizzes[largest_pdf]) <= 1:
            break
        per_pdf_quizzes[largest_pdf].pop(random.randrange(len(per_pdf_quizzes[largest_pdf])))
        total_questions -= 1

    # Combine final quiz
    combined_quiz = []
    for quiz in per_pdf_quizzes.values():
        combined_quiz.extend(quiz)

    # 🔴 ADD THIS (ID injection)
    for idx, q in enumerate(combined_quiz):
        if "id" not in q or not q["id"]:
            q["id"] = f"q_{idx}"

    # Save quiz (by PDF names)
    save_quiz(pdf_paths, combined_quiz)

    mcq_count =  sum(1 for q in combined_quiz if q["type"] == "MCQ")

    saq_count =  sum(1 for q in combined_quiz if q["type"] == "SAQ")

    total_questions  =   len(combined_quiz)


    print("mcq_count --->   saq_count  ---->  total_questions-->   ",mcq_count,"--->",saq_count,"--->",total_questions)

    print("combined_quiz   gen  fin   ",combined_quiz)


    return jsonify({
        "total_questions": total_questions,
        "mcq_count": mcq_count,
        "saq_count": saq_count,
        "quiz": combined_quiz
    })


# ======================================================
# 2️⃣ SUBMIT QUIZ (MCQ AUTO, SAQ STORED)
# ======================================================
@app.route("/submit_quiz/", methods=["POST"])
def submit_quiz():
    try:
        data = request.get_json()
        print("Received data:", data)  # Debug what frontend sent
        # Your quiz saving logic here
        pdf_names = data.get("pdf_names")
        mcq_answers = data.get("mcq_answers", {})
        saq_answers = data.get("saq_answers", {})
        user_id = str(uuid.uuid4())

    
        if not pdf_names:
            return jsonify({"error": "Missing pdf_names"}), 400
        # Load saved quiz to evaluate MCQs
        saved_quiz_data = load_existing_quiz(pdf_names)
        saved_quiz = saved_quiz_data.get("quiz", [])

        mcq_score = 0
        mcq_total = 0
        evaluated_mcqs = []

        for idx, q in enumerate(saved_quiz):
            if not isinstance(q, dict):
                continue  # skip invalid entries

            if q.get("type") == "MCQ":
                mcq_total += 1
                # Use existing ID or fallback to index-based ID
                qid = q.get("id") or f"q_{idx}"
                user_ans = mcq_answers.get(qid, "")
                is_correct = user_ans == q.get("correct_answer")

                if is_correct:
                    mcq_score += 1

                evaluated_mcqs.append({
                    "question_id": qid,
                    "user_answer": user_ans,
                    "correct_answer": q.get("correct_answer"),
                    "is_correct": is_correct
                })

        # Save attempt (MCQs + SAQs)
        attempt_record = {
            "mcq_score": mcq_score,
            "mcq_total": mcq_total,
            "mcq_details": evaluated_mcqs,
            "saq_answers": saq_answers,
            "saq_status": "pending"
        }

        save_user_attempt(user_id, pdf_names, attempt_record)

        return jsonify({
            "message": "Quiz submitted successfully",
            "mcq_score": mcq_score,
            "mcq_total": mcq_total,
            "saq_pending": len(saq_answers)
        })
    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}, 500

# ======================================================
if __name__ == "__main__":
    host_ip = get_local_ip()
    print(f"🚀 EvalAI_5   application   running on http://{host_ip}:8005")

    app.run(
        host=host_ip,
        port=8005,
        debug=True
    )
