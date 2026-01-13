let quizData = { mcq: [], saq: [] };
let quiz = [];
let mcqAnswers = {};
let saqAnswers = {};
let uploadedFiles = [];
let currentStage = "MCQ";

async function uploadPDFs() {
  const input = document.getElementById("pdfs");
  const status = document.getElementById("status");

  if (!input.files.length) {
    alert("Please select at least one PDF");
    return;
  }

  uploadedFiles = Array.from(input.files);

  const formData = new FormData();
  uploadedFiles.forEach(f => formData.append("files", f));

  status.innerText = "Generating quiz...";

  const res = await fetch("/upload_pdfs/", {
    method: "POST",
    body: formData
  });

  const data = await res.json();

  quizData.mcq = data.quiz.filter(q => q.type === "MCQ");
  quizData.saq = data.quiz.filter(q => q.type === "SAQ");

  window.location.href = "/quiz";
}

document.addEventListener("DOMContentLoaded", () => {
  if (window.location.pathname === "/quiz") {
    renderMCQs();
  }
});

function renderMCQs() {
  const container = document.getElementById("quiz-container");
  container.innerHTML = "<h2>Multiple Choice Questions</h2>";

  quizData.mcq.forEach(q => {
    let html = `<div class="question"><p>${q.question}</p>`;
    q.options.forEach(opt => {
      html += `
        <label>
          <input type="radio" name="${q.id}"
                 onchange="mcqAnswers['${q.id}']='${opt}'">
          ${opt}
        </label><br>
      `;
    });
    html += "</div>";
    container.innerHTML += html;
  });

  container.innerHTML += `<button onclick="renderSAQs()">Next</button>`;
}

function renderSAQs() {
  const container = document.getElementById("quiz-container");
  container.innerHTML = "<h2>Short Answer Questions</h2>";

  quizData.saq.forEach(q => {
    container.innerHTML += `
      <div class="question">
        <p>${q.question}</p>
        <textarea oninput="saqAnswers['${q.id}']=this.value"></textarea>
      </div>
    `;
  });

  container.innerHTML += `<button onclick="submitQuiz()">Submit Quiz</button>`;
}

async function submitQuiz() {
  const payload = {
    pdf_names: uploadedFiles.map(f => f.name),
    mcq_answers: mcqAnswers,
    saq_answers: saqAnswers
  };

  await fetch("/submit_quiz/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  window.location.href = "/result";
}
