import React, { useState } from "react";
import "../styles/QuizDisplay.css";

/* eslint-disable no-useless-escape */

const LETTERS = ["A", "B", "C", "D"];

function sanitizeOptionText(opt) {
  if (!opt && opt !== 0) return "";
  let s = String(opt).trim();
  // remove obvious placeholders prefixes like "Option A -", "Topic A"
  s = s.replace(/^(option|topic)\s*[A-D]?\s*[:\-–—\)]*\s*/i, "");
  // remove leading letter + dot "A. " or "A) "
  s = s.replace(/^[A-D]\s*[\.\)\-:]\s*/i, "");
  // collapse whitespace
  s = s.replace(/\s+/g, " ").trim();
  return s;
}

export default function QuizDisplay({ quizData }) {
  const questions = quizData?.quiz_questions || [];
  const [selected, setSelected] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState(null);

  const onSelect = (qIdx, optionIdx) => {
    if (submitted) return;
    setSelected((prev) => ({ ...prev, [qIdx]: optionIdx }));
  };

  const onSubmit = () => {
    let correct = 0;
    questions.forEach((q, i) => {
      const selIdx = selected[i];
      const selText = selIdx >= 0 ? sanitizeOptionText(q.options[selIdx]) : null;
      const answerText = sanitizeOptionText(q.answer || q.options?.[0] || "");
      if (selText && selText === answerText) correct++;
    });
    setScore(correct);
    setSubmitted(true);
  };

  const onReset = () => {
    setSelected({});
    setSubmitted(false);
    setScore(null);
  };

  return (
    <div className="quiz-display-container">
      <div className="quiz-header">
        <h2 className="quiz-title">{quizData?.title}</h2>
      </div>

      <div className="quiz-questions">
        <h3 className="questions-count">Questions ({questions.length})</h3>

        {questions.map((q, qi) => {
          const opts = (q.options || []).slice(0, 4).map(sanitizeOptionText);
          // ensure 4 options
          while (opts.length < 4) opts.push("N/A");
          const correctText = sanitizeOptionText(q.answer || opts[0]);

          return (
            <div key={qi} className="question-card">
              <div className="question-top">
                <div className="question-number">Q{qi + 1}.</div>
                <div className="question-text">{q.question}</div>
              </div>
              <div className="meta">
                <small>{q.difficulty || "medium"} • {q.section || "Intro"}</small>
              </div>

              <div className="options-list">
                {opts.map((opt, oi) => {
                  const isSelected = selected[qi] === oi;
                  const isCorrect = submitted && opt === correctText;
                  const isWrongSelected = submitted && isSelected && !isCorrect;

                  return (
                    <label
                      key={oi}
                      className={`option-row ${isSelected ? "selected" : ""} ${isCorrect ? "correct" : ""} ${isWrongSelected ? "wrong" : ""}`}
                    >
                      <input
                        type="radio"
                        name={`q-${qi}`}
                        checked={isSelected || false}
                        onChange={() => onSelect(qi, oi)}
                        disabled={submitted}
                      />
                      <div className="option-letter">{LETTERS[oi]}</div>
                      <div className="option-text">{opt}</div>
                    </label>
                  );
                })}
              </div>

              {submitted && (
                <div className="explanation-box">
                  <strong>Explanation:</strong> {q.explanation || "Based on the article summary and title"}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="quiz-actions">
        {!submitted ? (
          <button className="btn-submit" onClick={onSubmit}>Submit Quiz</button>
        ) : (
          <button className="btn-reset" onClick={onReset}>Reset Quiz</button>
        )}
      </div>

      {score !== null && (
        <div className="score-block">
          <h3>Your Score: {score} / {questions.length}</h3>
          <p>{Math.round((score / Math.max(1, questions.length)) * 100)}%</p>
        </div>
      )}

      <div className="related-topics">
        <h4>Related Topics</h4>
        <div className="topics-list">
          {(quizData?.related_topics || []).map((t, i) => <span key={i} className="topic-pill">{t}</span>)}
        </div>
      </div>
    </div>
  );
}
