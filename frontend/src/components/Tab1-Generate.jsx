import React, { useState } from 'react';
import axios from 'axios';
import QuizDisplay from './QuizDisplay';
import '../styles/Tab1.css';

const API_URL = 'https://wikipediaquizgenerator.onrender.com/api/quiz';

function Tab1Generate() {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [quizData, setQuizData] = useState(null);

    const handleGenerateQuiz = async (e) => {
        e.preventDefault();
        if (!url.trim()) {
            setError('Please enter a Wikipedia URL');
            return;
        }
        setLoading(true);
        setError('');
        setQuizData(null);
        try {
            const response = await axios.post(`${API_URL}/generate`, null, {
                params: { url: url.trim() }
            });
            setQuizData(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to generate quiz. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <div>
                <h2>Enter Wikipedia Article URL</h2>
                <form onSubmit={handleGenerateQuiz}>
                    <input
                        type="text"
                        placeholder="e.g., https://en.wikipedia.org/wiki/Alan_Turing"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        className="url-input"
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        className="generate-button"
                        disabled={loading}
                    >
                        {loading ? 'Generating...' : '✨ Generate Quiz'}
                    </button>
                </form>
                {error && <div>{error}</div>}
            </div>
            {quizData && <QuizDisplay quizData={quizData} />}
            {loading && (
                <div>
                    <div></div>
                    <p>Scraping Wikipedia and generating quiz questions...</p>
                </div>
            )}
        </div>
    );
}

export default Tab1Generate;
