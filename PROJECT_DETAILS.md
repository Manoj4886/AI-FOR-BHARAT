# 🧠 Saarathi — Smart AI Teacher

> An AI-powered interactive teaching platform that uses a lip-synced avatar, voice I/O, adaptive skill levels, and 15+ AWS services to deliver personalized, cinematic learning experiences.

---

## 📌 Project Overview

| Field | Details |
|---|---|
| **Project Name** | Saarathi — Smart AI Teacher |
| **Version** | 2.0.0 |
| **Type** | Full-Stack Web Application |
| **Architecture** | Vite + React SPA ↔ FastAPI REST API ↔ AWS + Groq + Supabase |
| **Deployment** | Frontend: Vercel · Backend: Railway / Render |
| **License** | Hackathon project (Hack4Impact) |

---

## 🏗️ Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| **React 19** | UI framework |
| **Vite 7** | Dev server & bundler |
| **Three.js / R3F** | 3D avatar rendering (`@react-three/fiber`, `@react-three/drei`) |
| **Recharts 3** | Progress dashboard charts |
| **Mermaid** | Flow diagram rendering |
| **Axios** | HTTP client for API calls |
| **Web Speech API** | Browser-native voice input (STT) |
| **SpeechSynthesis API** | Browser-native voice output (TTS) with lip-sync |

### Backend
| Technology | Purpose |
|---|---|
| **FastAPI** | Python REST API framework |
| **Uvicorn** | ASGI server |
| **Groq API** | LLM inference (LLaMA 3.3-70B) |
| **Supabase** | PostgreSQL database (progress tracking) |
| **Boto3** | AWS SDK for Python |
| **Pydantic v2** | Request/response validation |
| **HTTPX** | Async HTTP client |
| **Pillow / NumPy / imageio** | Image & video processing |
| **PyPDF2 / python-docx** | Document text extraction |
| **Mangum** | AWS Lambda adapter |

### AWS Services (15 integrations)
| Service | Purpose |
|---|---|
| **Amazon Bedrock** | Claude 3 Haiku for AI explanations (alternative to Groq) |
| **Amazon Polly** | Neural text-to-speech with viseme speech marks |
| **Amazon S3** | File storage (avatars, uploads, generated media) |
| **Amazon Rekognition** | Image analysis & label detection |
| **Amazon Kinesis Video** | Live video streaming (DeepLens integration) |
| **Amazon Q** | AI-assisted content review & expert answers |
| **Amazon A2I** | Augmented AI / human-in-the-loop review |
| **AWS Security Hub** | Security findings & compliance monitoring |
| **Amazon SageMaker** | ML visualizations & learning analytics |
| **Conversational AI** | Multi-turn conversation memory |
| **Avatar Engines** | Server-side avatar expression generation |
| **Generative AI Video** | AI video generation from images |
| **Amazon Nova Reel** | Advanced video generation pipeline |
| **Elemental MediaConvert** | Video transcoding & processing |
| **AWS DeepLens** | Edge ML inference on video streams |

---

## 📂 Project Structure

```
hack4impact/
├── backend/                          # FastAPI Python backend
│   ├── main.py                       # App entry point (16 routers mounted)
│   ├── config.py                     # Environment variables loader
│   ├── models.py                     # Pydantic request/response models
│   ├── requirements.txt              # Python dependencies
│   ├── lambda_handler.py             # AWS Lambda adapter (Mangum)
│   ├── .env / .env.example           # Environment configuration
│   │
│   ├── routers/                      # API route handlers (17 files)
│   │   ├── ask.py                    # POST /ask, POST /ask-with-file
│   │   ├── quiz.py                   # POST /quiz
│   │   ├── progress.py              # GET/POST /progress
│   │   ├── vision.py                 # POST /generate-image, /generate-video
│   │   ├── storage.py               # S3 file upload/download
│   │   ├── recommend.py             # Topic recommendations
│   │   ├── video_stream.py          # Kinesis Video + DeepLens
│   │   ├── auth.py                  # User authentication
│   │   ├── amazon_q.py             # Amazon Q review/expert answers
│   │   ├── human_review.py         # A2I human-in-the-loop
│   │   ├── security.py             # Security Hub findings
│   │   ├── sagemaker.py            # ML visualizations
│   │   ├── conversation.py         # Multi-turn conversations
│   │   ├── avatar_engines.py       # Avatar expression engine
│   │   ├── generative_video.py     # AI video generation
│   │   ├── nova_reel.py            # Nova Reel video pipeline
│   │   └── mediaconvert.py         # Video transcoding
│   │
│   └── services/                     # Business logic layer (18 files)
│       ├── groq_service.py           # Groq LLaMA 3.3-70B integration
│       ├── bedrock_service.py        # Amazon Bedrock (Claude 3) integration
│       ├── polly_service.py          # Amazon Polly TTS + speech marks
│       ├── s3_service.py             # S3 CRUD operations
│       ├── rekognition_service.py    # Image analysis
│       ├── supabase_service.py       # Supabase DB operations
│       ├── image_service.py          # Bedrock image generation
│       ├── video_service.py          # Video slideshow generation
│       ├── kinesis_video_service.py  # Kinesis Video Streams
│       ├── amazon_q_service.py       # Amazon Q integration
│       ├── a2i_service.py            # Augmented AI workflows
│       ├── security_hub_service.py   # Security Hub service
│       ├── sagemaker_service.py      # SageMaker analytics
│       ├── conversation_service.py   # Conversation memory
│       ├── avatar_engine_service.py  # Avatar engine logic
│       ├── generative_video_service.py  # Gen AI video
│       ├── nova_reel_service.py      # Nova Reel service
│       └── mediaconvert_service.py   # MediaConvert service
│
├── frontend/                         # Vite + React SPA
│   ├── index.html                    # HTML entry
│   ├── package.json                  # Node dependencies
│   ├── vite.config.js                # Vite configuration
│   └── src/
│       ├── main.jsx                  # React root mount
│       ├── App.jsx                   # App shell (auth, speech, routing)
│       ├── index.css                 # Full design system (~80KB)
│       │
│       ├── components/               # React UI components (18 files)
│       │   ├── AuthPage.jsx          # Login/signup UI
│       │   ├── AuthPage.css          # Auth page styles
│       │   ├── TeacherPage.jsx       # Main teaching interface (largest)
│       │   ├── TeacherAvatar.jsx     # 2D animated teacher avatar
│       │   ├── TeacherAvatar.css     # Avatar animations
│       │   ├── AnimatedAvatar.jsx    # Advanced animated avatar
│       │   ├── AnimatedAvatar.css    # Advanced avatar styles
│       │   ├── CinematicAvatar.jsx   # Cinematic avatar variant
│       │   ├── Avatar.jsx            # SVG lip-sync avatar
│       │   ├── AvatarModel.jsx       # 3D avatar model (Three.js)
│       │   ├── GlassBoard.jsx        # Glassmorphism whiteboard
│       │   ├── Whiteboard.jsx        # Chalkboard display
│       │   ├── QuestionBar.jsx       # Input bar + mic button
│       │   ├── Quiz.jsx              # MCQ quiz component
│       │   ├── ProgressDashboard.jsx # Charts + history
│       │   ├── MermaidDiagram.jsx    # Flow diagram renderer
│       │   ├── VisionPanel.jsx       # AI vision/image display
│       │   └── TeacherCommandPanel.jsx # Admin controls
│       │
│       └── services/
│           └── api.js                # Axios API layer (86 functions)
│
└── supabase_schema.sql               # Database schema
```

---

## 🔌 API Endpoints

### Core Teaching
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ask` | Ask a question → get AI explanation, visuals, audio, diagrams |
| `POST` | `/ask-with-file` | Ask about an uploaded file (PDF, DOCX, TXT, image) |
| `POST` | `/quiz` | Generate MCQ quiz on a topic |
| `GET` | `/progress/{user_id}` | Get user's learning progress |
| `POST` | `/progress` | Log a learning event |
| `GET` | `/health` | API health check + AWS service status |

### Vision & Media
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/generate-image` | Generate educational image (Bedrock) |
| `POST` | `/generate-video` | Generate explainer video from image |
| `POST` | `/nova-reel/*` | Advanced video generation (Nova Reel) |
| `POST` | `/mediaconvert/*` | Video transcoding jobs |

### Storage & Streaming
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload` | Upload file to S3 |
| `GET` | `/download/{key}` | Download file from S3 |
| `GET` | `/video-streams/*` | Kinesis Video stream management |
| `GET` | `/hls-stream/{name}` | Get HLS streaming URL |

### AI Assist & Review
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/amazon-q/review` | AI content quality review |
| `POST` | `/amazon-q/expert` | Get expert answer via Amazon Q |
| `POST` | `/human-review/start` | Start A2I human review |
| `GET` | `/human-review/pending` | List pending reviews |
| `POST` | `/human-review/decide` | Submit review decision |

### Analytics & Security
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/sagemaker/dashboard` | Visualization dashboard |
| `GET` | `/sagemaker/timeline` | Learning timeline |
| `GET` | `/sagemaker/heatmap` | Topic heatmap |
| `GET` | `/security/findings` | Security Hub findings |
| `GET` | `/security/compliance` | Compliance status |
| `GET` | `/security/score` | Security score |

### Auth & Conversation
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/login` | User login |
| `POST` | `/auth/signup` | User registration |
| `GET` | `/conversation/history` | Get conversation history |
| `POST` | `/conversation/message` | Add message to conversation |

---

## 💾 Database Schema (Supabase / PostgreSQL)

### `questions` table
| Column | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Auto-generated |
| `user_id` | TEXT | User identifier |
| `question` | TEXT | Question asked |
| `skill_level` | TEXT | beginner / intermediate / advanced |
| `created_at` | TIMESTAMPTZ | Auto-timestamp |

### `quiz_scores` table
| Column | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Auto-generated |
| `user_id` | TEXT | User identifier |
| `topic` | TEXT | Quiz topic |
| `score` | INTEGER | Correct answers |
| `total` | INTEGER | Total questions |
| `created_at` | TIMESTAMPTZ | Auto-timestamp |

---

## ✨ Key Features

### 🎓 AI Teaching Engine
- **Dual LLM support**: Groq (LLaMA 3.3-70B) + AWS Bedrock (Claude 3 Haiku)
- **Adaptive skill levels**: Beginner → Intermediate → Advanced explanations
- **Structured JSON responses**: explanation, visual_scene, flow_diagram, spoken_text, code_blocks
- **Multi-turn conversations**: Context-aware follow-up questions
- **File analysis**: Upload PDF, DOCX, TXT, or images for discussion

### 🗣️ Voice & Avatar
- **Voice input**: Web Speech API (browser-native STT)
- **Voice output**: Amazon Polly neural TTS with viseme speech marks
- **Lip-sync avatar**: SVG/2D/3D teacher with mouth animation synced to speech
- **Cinematic design**: Glassmorphism panels, dark/light themes, micro-animations
- **Avatar expressions**: Content-reactive expressions driven by AI responses

### 📊 Visual Learning
- **Mermaid diagrams**: Auto-generated flow charts rendered in-browser
- **AI image generation**: Bedrock-powered educational images
- **Video generation**: Slideshow + narration from generated images
- **Glass whiteboard**: Typewriter-style animated text display

### 📝 Assessment
- **Auto-generated quizzes**: MCQ quiz on any topic, any skill level
- **Progress tracking**: Quiz scores, question history, learning timeline
- **Recharts dashboard**: Visual analytics (radar, heatmap, sparkline)

### 🔒 Enterprise Features
- **Human-in-the-loop review**: Amazon A2I for content accuracy verification
- **Security monitoring**: AWS Security Hub integration
- **Content quality scoring**: Amazon Q-powered review
- **Video streaming**: Kinesis Video + DeepLens for live classroom feeds

---

## 🔧 Environment Variables

```env
# AWS
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1

# Amazon Bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# Amazon Polly
POLLY_VOICE_ID=Matthew

# Amazon S3
S3_BUCKET_NAME=
S3_AVATAR_KEY=avatar/teacher.glb

# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=

# Groq (primary LLM)
GROQ_API_KEY=

# Kinesis Video
KINESIS_VIDEO_STREAM_NAME=saarathi-deeplens-stream
```

---

## 🚀 How to Run

### Backend
```bash
cd backend
pip install -r requirements.txt
# Configure .env with your API keys
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### Database
1. Create Supabase project at [supabase.com](https://supabase.com)
2. Run `supabase_schema.sql` in the SQL Editor
3. Copy Project URL + anon key to `.env`

---

## 📈 Project Stats

| Metric | Count |
|---|---|
| Backend routers | 17 |
| Backend services | 18 |
| Frontend components | 18 |
| API functions (frontend) | 86 |
| AWS service integrations | 15 |
| Pydantic data models | 10 |
| Database tables | 2 |
| Python dependencies | 15 |
| Node dependencies | 8 |
| Total backend files | ~40 |
| Total frontend files | ~25 |
| CSS design system | ~80 KB |
