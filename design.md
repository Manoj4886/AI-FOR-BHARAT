# 📐 Bolt AI Tutor (Saarathi App) – System Design Document

AI for Bharat Hackathon Submission

---

# 1️⃣ Design Overview

Bolt AI Tutor is designed as a scalable, cloud-native AI learning platform that delivers real-time personalized video-based teaching using AWS AI services.

The system follows a modular, layered architecture to ensure:

- Scalability
- Low latency
- High availability
- Cost efficiency
- Security
- Adaptability

---

# 2️⃣ High-Level Architecture

The system is divided into 5 primary layers:

1. User Layer
2. Frontend Layer
3. Backend API Layer
4. AI Processing Layer
5. Data & Storage Layer

---

# 3️⃣ System Architecture Design

## 3.1 User Layer

Actors:
- Students
- Developers

Access Platforms:
- Web Application
- Mobile Application

Responsibilities:
- Topic selection
- Skill level selection
- Voice/text doubt input
- Viewing AI video lessons
- Taking quizzes
- Tracking progress

---

## 3.2 Frontend Layer

Technologies:
- React.js (Web)
- Flutter (Mobile)

Responsibilities:
- UI rendering
- User session handling
- API communication
- Real-time video display
- Input collection (voice/text)

Design Principles:
- Minimal UI
- Clean dashboard
- Low bandwidth optimization
- Accessibility-first design

---

## 3.3 Backend API Layer

Technology:
- FastAPI (Python)
- RESTful APIs
- JWT Authentication

Responsibilities:
- Request validation
- Authentication & authorization
- Routing to AI services
- Session management
- Data aggregation

---

## 3.4 AI Processing Layer

Core Components:

### 1️⃣ Content Generation Engine
- Amazon Bedrock (LLM)
- Generates structured lessons dynamically

### 2️⃣ Speech Processing
- Amazon Transcribe (Speech-to-Text)
- Amazon Polly (Text-to-Speech)

### 3️⃣ Personalization Engine
- Skill-level detection
- Learning pattern analysis
- Adaptive difficulty control

### 4️⃣ Avatar Video Engine
- Converts AI-generated content into realistic video format
- Synchronizes voice with avatar rendering

---

## 3.5 Data & Storage Layer

Technologies:
- Amazon DynamoDB (User progress & analytics)
- Amazon S3 (Video storage)
- CloudFront (Content delivery)

Responsibilities:
- Store user learning history
- Store quiz performance
- Store lesson metadata
- Deliver cached content efficiently

---

# 4️⃣ Design Flow

## Step 1:
User selects topic & level

## Step 2:
Frontend sends API request

## Step 3:
Backend validates request

## Step 4:
AI Engine generates lesson

## Step 5:
Speech + Avatar rendering

## Step 6:
Video delivered to user

## Step 7:
Performance stored & personalization updated

---

# 5️⃣ Data Flow Design

User Input  
→ API Gateway  
→ FastAPI Backend  
→ AI Engine (Bedrock)  
→ Personalization Engine  
→ Video Rendering  
→ S3 Storage  
→ Delivered via CloudFront  

Analytics stored in DynamoDB.

---

# 6️⃣ Scalability Design

- Auto-scaling EC2 instances
- AWS Lambda for serverless operations
- CDN-based video distribution
- Cached AI responses for common topics

Designed to support 10,000+ concurrent users.

---

# 7️⃣ Security Design

- JWT-based authentication
- AWS IAM role-based access control
- Encrypted API communication (HTTPS)
- Secure cloud storage policies
- Input validation to prevent injection attacks

---

# 8️⃣ Performance Optimization Strategy

- AI response caching
- Video pre-rendering for popular lessons
- Adaptive streaming
- Lightweight frontend rendering
- Serverless event-based execution

---

# 9️⃣ Design Constraints

- Cost optimization (Hackathon budget)
- Low latency for AI response
- Limited bandwidth support (Rural users)
- Cloud dependency (AWS-native)

---

# 🔟 Future Design Enhancements

- AR/VR classroom integration
- Offline learning sync mode
- AI interview simulator module
- Multi-language expansion engine
- Real-time collaborative classroom mode

---

# 📌 Conclusion

The system design ensures modularity, scalability, and efficient AI-driven content delivery using AWS cloud services.

Bolt AI Tutor is architected to transform passive learning into an intelligent, adaptive, and scalable digital mentorship experience across Bharat.

---

© 2026 Bolt AI Tutor – AI for Bharat Hackathon
