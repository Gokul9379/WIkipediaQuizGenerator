
DeepKlarity is a full-stack web application that automatically generates interactive quizzes from **Wikipedia articles** using **AI**.  
It allows users to paste any Wikipedia URL, auto-generate questions and answers, view previous quizzes, and review their scores — all in one platform.

---

## 🚀 Features

✅ **AI-Powered Quiz Generation**  
- Fetches article content and sections using a smart Wikipedia scraper.  
- Generates multiple-choice questions and answers automatically using AI.  

✅ **Quiz History Tracking**  
- Stores every generated quiz in a local SQLite database.  
- View, delete, or revisit quizzes anytime.  

✅ **Score Management**  
- Allows users to take quizzes and record their scores.  
- Displays score, total questions, and attempt timestamp in history details.  

✅ **Beautiful & Responsive Frontend**  
- React-based interface for quiz generation and review.  
- Modal view for quiz details and question breakdown.

---

## 🧩 Tech Stack

| Layer | Technology |
|-------|-------------|
| **Frontend** | React, Axios, HTML, CSS |
| **Backend** | FastAPI (Python) |
| **Database** | SQLite (via SQLAlchemy ORM) |
| **AI/Quiz Generation** | LangChain + Google Gemini / LLM APIs |
| **Other Tools** | Pydantic, Uvicorn, Requests |

---

## 📁 Project Structure

```

DeepKlarity/
├── backend/
│   ├── app/
│   │   ├── crud.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── routes/
│   │   │   └── quiz.py
│   │   ├── schemas.py
│   │   └── utils/
│   │       ├── scraper.py
│   │       └── quiz_generator.py
│   ├── app.db
│   ├── requirements.txt
│   └── venv/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Tab1Generate.jsx
│   │   │   ├── Tab2History.jsx
│   │   │   ├── QuizDisplay.jsx
│   │   │   └── Modal.jsx
│   │   ├── styles/
│   │   └── App.js
│   ├── package.json
│   └── README.md
└── README.md

````

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/DeepKlarity.git
cd DeepKlarity
````

---

### 2️⃣ Backend Setup (FastAPI)

```bash
cd backend
python -m venv venv
venv\Scripts\activate       # On Windows
# source venv/bin/activate  # On Linux/Mac

pip install -r requirements.txt
```

#### Run the Backend Server:

```bash
uvicorn app.main:app --reload
```

Server will start at **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

Visit the **Swagger Docs** at:
👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### 3️⃣ Frontend Setup (React)

```bash
cd frontend
npm install
npm start
```

Frontend will start at **[http://localhost:3000](http://localhost:3000)**

Make sure backend (port 8000) is running before using the app.

---

## 🧠 How It Works

1. Enter a **Wikipedia URL** in the “Generate Quiz” tab.
2. The backend scrapes and summarizes the article.
3. The AI model generates a set of quiz questions, answers, and explanations.
4. The quiz is stored in the local SQLite database.
5. You can view, delete, or retake it from the **Quiz History** tab.
6. When you submit your answers, the score and timestamp are saved and visible in details.

---

## 📊 API Endpoints (Summary)

| Method   | Endpoint                 | Description                              |
| -------- | ------------------------ | ---------------------------------------- |
| `POST`   | `/api/quiz/generate`     | Generate a new quiz from a Wikipedia URL |
| `GET`    | `/api/quiz/history`      | Get list of all quizzes                  |
| `GET`    | `/api/quiz/history/{id}` | Get quiz details by ID                   |
| `DELETE` | `/api/quiz/history/{id}` | Delete a quiz                            |
| `POST`   | `/api/quiz/submit`       | Record submitted score & attempt time    |

---

## 🧾 Example `.env` (optional)

If you use Google Gemini or OpenAI API for quiz generation:

```
GEMINI_API_KEY=your_api_key_here
OPENAI_API_KEY=your_openai_key_here
```

Then load it in `quiz_generator.py`.

---

## 🧰 Dependencies (Backend)

Main dependencies in `requirements.txt`:

```
fastapi
uvicorn
sqlalchemy
pydantic
requests
langchain
google-generativeai
```

---

## 📸 Screenshots (Recommended)

*(Add screenshots here once available)*

| Generate Quiz                    | Quiz History                   |
| -------------------------------- | ------------------------------ |
| ![generate](assets/generate.png) | ![history](assets/history.png) |

---

## 🧑‍💻 Developers

**Project Name:** DeepKlarity
**Developed by:** Gokul P and Team
**Institution:** SNS College of Technology
**Domain:** AI + Full Stack Development

---

## ⭐ Future Enhancements

* Add user login / profiles
* Enable category-based quiz filtering
* Add export to PDF / share results
* Integrate with GPT-5 or Gemini-Pro for better question quality

---

## 🏁 License

MIT License © 2025 — Gokul P
Feel free to fork, modify, and improve 🎯

---

## ❤️ Acknowledgements

* [FastAPI](https://fastapi.tiangolo.com) — for the blazing-fast backend
* [React.js](https://react.dev) — for interactive UI
* [Wikipedia API](https://www.wikipedia.org/) — for article data
* [LangChain](https://www.langchain.com) & [Gemini AI](https://ai.google.dev) — for question generation


