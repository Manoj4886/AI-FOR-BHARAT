<<<<<<< HEAD
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
=======
#  Bolt AI Tutor (Saarathi App)

AI-Powered Real-Time Personalized Video Learning Platform  
Built for AWS AI for Bharat Hackathon 2026

---

##  Overview

Bolt AI Tutor is an AI-powered learning platform that transforms passive video education into an interactive, personalized, two-way learning experience.

It provides a realistic AI video mentor that:
- Teaches concepts step-by-step
- Adapts explanations based on learner level
- Resolves doubts instantly (voice or text)
- Tracks progress and personalizes future lessons

Designed specifically for students and developers across India 🇮🇳

---

##  Problem Statement

Current learning platforms:
- Provide static, pre-recorded content
- Do not adapt to individual learners
- Lack real-time doubt resolution
- Are not optimized for rural accessibility

Learning is scalable, but not personalized.

---

##  Our Solution

Bolt AI Tutor introduces:

-  Real-time AI-generated video teaching
-  Adaptive personalization engine
-  Voice-based doubt interaction
-  Learning analytics dashboard
-  Scalable AWS-native cloud architecture

An AI mentor that teaches like a human and adapts like a coach.

---

##  System Architecture

The system follows a layered architecture:

User Layer  
→ Frontend (React / Flutter)  
→ Backend (FastAPI)  
→ AI Engine (Amazon Bedrock, Transcribe, Polly)  
→ Data Layer (DynamoDB, S3, CloudFront)

For detailed architecture, refer to `design.md`.

---

##  Tech Stack

###  AI Services
- Amazon Bedrock (LLM)
- Amazon Transcribe (Speech-to-Text)
- Amazon Polly (Text-to-Speech)

###  Cloud
- AWS EC2
- AWS Lambda
- Amazon API Gateway
- Amazon CloudFront

###  Database & Storage
- Amazon DynamoDB
- Amazon S3

###  Frontend
- React.js (Web)
- Flutter (Mobile)

###  Security
- AWS IAM
- JWT Authentication
- HTTPS Encryption

---

##  Core Features

- Smart onboarding & skill detection
- AI-generated dynamic lessons
- Realistic AI avatar video teaching
- Real-time doubt solving
- Adaptive difficulty adjustment
- Practice & quiz module
- Learning progress tracking
- Low-bandwidth support mode

---

##  Estimated Cost (MVP)

₹12,000 – ₹15,000 per month (AWS-based)

Covered using AWS Hackathon Credits during development phase.

---

##  Getting Started (Development Setup)

### Prerequisites
- Python 3.10+
- Node.js 18+
- Flutter SDK
- AWS CLI configured
- Git

### Clone Repository
```bash
git clone https://github.com/your-repo/bolt-ai-tutor.git
cd bolt-ai-tutor
>>>>>>> c89cea7c30cd104eb9836933d24ba397174ce730
