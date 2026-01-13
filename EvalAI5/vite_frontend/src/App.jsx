import React, { useState } from "react";
import QuizScreen from "./QuizScreen";

function App() {
  const [files, setFiles] = useState([]);
  const [activeQuiz, setActiveQuiz] = useState(null);
  const [mcqAnswers, setMcqAnswers] = useState({});
  const [saqAnswers, setSaqAnswers] = useState({});
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState("UPLOAD"); 
  // "UPLOAD" -> "MCQ" -> "SAQ" -> "SUBMIT"

  // File upload
  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
  };
  const handleSubmitPDFs = async () => {
    if (files.length === 0) {
      alert("Please select at least one PDF");
      return;
    }

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    setLoading(true);
    try {
      const res = await fetch("http://localhost:5000/upload_pdfs/", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      const mcq = data.quiz.filter((q) => q.type === "MCQ");
      const saq = data.quiz.filter((q) => q.type === "SAQ");

      setActiveQuiz({ mcq, saq });
      setMcqAnswers({});
      setSaqAnswers({});
      setStage("MCQ"); // Start with MCQ stage
    } catch (err) {
      console.error(err);
      alert("Error uploading PDFs or generating quiz");
    }
    setLoading(false);
  };

  // Answer handlers
  const handleMcqAnswer = (id, option) => {
    setMcqAnswers((prev) => ({ ...prev, [id]: option }));
  };
  const handleSaqAnswer = (id, text) => {
    setSaqAnswers((prev) => ({ ...prev, [id]: text }));
  };

  // Submit quiz
  const submitUserQuiz = async () => {
    if (!activeQuiz) return;

    const payload = {
        pdf_names: files.map((f) => f.name),
        mcq_answers: mcqAnswers,
      saq_answers: saqAnswers,
    };


    try {
      const res = await fetch("http://localhost:5000/submit_quiz/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      alert("Quiz submitted successfully!");
      console.log("Submission response:", data);

      // Reset everything
      setActiveQuiz(null);
      setMcqAnswers({});
      setSaqAnswers({});
      setFiles([]);
      setStage("UPLOAD");
    } catch (err) {
      console.error(err);
      alert("Error submitting quiz");
    }
  };

  return (
    <div className="flex flex-col items-center justify-start min-h-screen p-6 bg-gray-100 mt-12">
      <h1 className="text-3xl font-bold mb-6 text-center">Quiz Generator</h1>

      {/* File upload */}
      {stage === "UPLOAD" && (
        <div className="mb-4">
          <input
            type="file"
            multiple
            accept="application/pdf"
            onChange={handleFileChange}
            className="border p-2 rounded"
          />
          <button
            onClick={handleSubmitPDFs}
            className="ml-4 bg-blue-600 text-white px-4 py-2 rounded"
          >
            Generate Quiz
          </button>
        </div>
      )}

      {loading && <p>Loading quiz...</p>}

      {/* MCQ Stage */}
      {stage === "MCQ" && activeQuiz?.mcq.length > 0 && (
        <div className="w-full max-w-xl">
          <QuizScreen
            questions={activeQuiz.mcq}
            type="MCQ"
            onAnswerChange={handleMcqAnswer}
            answers={mcqAnswers}
            onFinish={() => setStage("SAQ")} // custom prop to signal finish
          />
        </div>
      )}

      {/* SAQ Stage */}
      {stage === "SAQ" && activeQuiz?.saq.length > 0 && (
        <div className="w-full max-w-xl">
          <QuizScreen
            questions={activeQuiz.saq}
            type="SAQ"
            onAnswerChange={handleSaqAnswer}
            answers={saqAnswers}
            onFinish={() => setStage("SUBMIT")}
          />
        </div>
      )}

      {/* Submit Stage */}
      {stage === "SUBMIT" && (
        <div className="flex flex-col items-center mt-6">
          <h2 className="text-2xl font-bold mb-4">Quiz Completed!</h2>
          <button
            onClick={() => submitUserQuiz("")}
            className="bg-purple-700 text-white px-6 py-2 rounded"
          >
            Submit Quiz
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
