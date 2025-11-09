import React, { useState } from 'react';
import Tab1Generate from './components/Tab1-Generate';   // Create this file next!
import Tab2History from './components/Tab2-History';     // Create this file next!
import './App.css';                                      // Optional for main styling

function App() {
  const [activeTab, setActiveTab] = useState('generate');

  return (
    <div className="app">
      <header className="header">
        <h1>🧠 DeepKlarity</h1>
        <p>AI-Powered Wikipedia Quiz Generator</p>
      </header>

      <nav className="tabs">
        <button
          className={`tab-button ${activeTab === 'generate' ? 'active' : ''}`}
          onClick={() => setActiveTab('generate')}
        >
          📝 Generate Quiz
        </button>
        <button
          className={`tab-button ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          📚 Quiz History
        </button>
      </nav>

      <main className="content">
        {activeTab === 'generate' && <Tab1Generate />}
        {activeTab === 'history' && <Tab2History />}
      </main>

      <footer className="footer">
        <p>© 2025 DeepKlarity Technologies. Powered by Google Gemini API.</p>
      </footer>
    </div>
  );
}

export default App;
