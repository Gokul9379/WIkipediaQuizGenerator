import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Modal from './Modal';
import QuizDisplay from './QuizDisplay';
import '../styles/Tab2.css';

const API_URL = 'https://wikipediaquizgenerator.onrender.com/api/quiz';

function Tab2History() {
  const [quizzes, setQuizzes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedQuiz, setSelectedQuiz] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchQuizHistory();
  }, []);

  const fetchQuizHistory = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/history?limit=50`);
      setQuizzes(response.data);
    } catch (err) {
      setError('Failed to load quiz history');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = (quiz) => {
    setSelectedQuiz(quiz);
    setShowModal(true);
  };

  const handleDelete = async (quizId) => {
    if (window.confirm('Are you sure you want to delete this quiz?')) {
      try {
        await axios.delete(`${API_URL}/history/${quizId}`);
        setQuizzes(quizzes.filter((q) => q.id !== quizId));
      } catch (err) {
        setError('Failed to delete quiz');
      }
    }
  };

  return (
    <div>
      <h2>Quiz History</h2>
      {error && <div>{error}</div>}
      {loading ? (
        <div>
          <div></div>
          <p>Loading quiz history...</p>
        </div>
      ) : quizzes.length === 0 ? (
        <div>
          <p>No quizzes generated yet. Go to the "Generate Quiz" tab to get started!</p>
        </div>
      ) : (
        <div>
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>URL</th>
                <th>Generated</th>
                <th>Questions</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {quizzes.map((quiz) => (
                <tr key={quiz.id}>
                  <td className="title">{quiz.title}</td>
                  <td className="url">
                    <a href={quiz.url} target="_blank" rel="noopener noreferrer">
                      View
                    </a>
                  </td>
                  <td className="date">
                    {(() => {
                      // Try a few common timestamp fields and guard against invalid dates
                      const ts = quiz.created_at || quiz.generated_at || quiz.createdAt;
                      if (!ts) return "N/A";
                      const d = new Date(ts);
                      return isNaN(d.getTime()) ? "N/A" : d.toLocaleString();
                    })()}
                  </td>
                  <td className="questions">
                    {quiz.quiz_questions?.length || 0}
                  </td>
                  <td className="actions">
                    <button
                      className="btn-details"
                      onClick={() => handleViewDetails(quiz)}
                    >
                      Details
                    </button>
                    <button
                      className="btn-delete"
                      onClick={() => handleDelete(quiz.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {showModal && selectedQuiz && (
        <Modal isOpen={showModal} onClose={() => setShowModal(false)}>
          <QuizDisplay quizData={selectedQuiz} />
        </Modal>
      )}
    </div>
  );
}

export default Tab2History;
