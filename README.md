# 🧠 Smart AI Teacher MVP

An AI-powered interactive teacher app using **100% free tools**.

## Tech Stack

| Feature | Tool |
|---|---|
| AI Explanations | Groq API (LLaMA 3.3-70B) |
| Voice Input | Web Speech API (browser native) |
| Voice Output | Browser SpeechSynthesis (lip-synced avatar) |
| Frontend | Vite + React |
| Database | Supabase (PostgreSQL) |
| Hosting | Vercel |
| Backend | FastAPI (Python) |

---

## 🚀 Getting Started

### 1. Set up Supabase
1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to **SQL Editor** and run `supabase_schema.sql`
4. Copy your `Project URL` and `anon public key` from **Settings → API**

### 2. Get Groq API Key
1. Sign up free at [console.groq.com](https://console.groq.com)
2. Create an API key

### 3. Backend Setup
```bash
cd backend
copy .env.example .env
# Edit .env with your keys
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## 📁 Project Structure

```
hack4impact/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── config.py                # Env vars
│   ├── models.py                # Pydantic models
│   ├── routers/
│   │   ├── ask.py               # POST /ask
│   │   ├── quiz.py              # POST /quiz
│   │   └── progress.py          # GET/POST /progress
│   ├── services/
│   │   ├── groq_service.py      # Groq LLaMA integration
│   │   └── supabase_service.py  # Supabase CRUD
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Avatar.jsx           # Animated lip-sync SVG avatar
│       │   ├── Whiteboard.jsx       # Typewriter chalkboard panel
│       │   ├── QuestionBar.jsx      # Question input + mic
│       │   ├── Quiz.jsx             # MCQ quiz component
│       │   └── ProgressDashboard.jsx # Charts + history
│       ├── services/api.js          # Axios API layer
│       ├── App.jsx                  # App shell + SpeechSynthesis
│       └── index.css                # Full design system
└── supabase_schema.sql
```

---

## ✨ Features

- **🎤 Voice Input** — Click the mic, speak your question (Web Speech API)
- **🗣️ Lip-Sync Avatar** — SVG teacher face animates mouth while speaking
- **📋 Chalkboard Whiteboard** — Typewriter-style animated explanation
- **🧠 Adaptive Skill Levels** — Beginner / Intermediate / Advanced explanations
- **📝 Quiz Mode** — Auto-generated MCQ quiz on any topic
- **📊 Progress Dashboard** — Quiz scores, question history, Recharts charts

---

## 🌐 Deploying to Vercel (Frontend)

1. Push your repo to GitHub
2. Go to [vercel.com](https://vercel.com), import your repo
3. Set **Root Directory** = `frontend`
4. Add env var: `VITE_API_URL=https://your-backend-url`
5. Deploy!

For the backend, deploy to [Railway](https://railway.app) or [Render](https://render.com) (both free tiers available).
