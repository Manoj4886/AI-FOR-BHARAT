# 🚀 Bolt AI Tutor (Saarathi App)

AI-Powered Real-Time Personalized Video Learning Platform  
Built for AWS AI for Bharat Hackathon 2026

---

## 📌 Overview

Bolt AI Tutor is an AI-powered learning platform that transforms passive video education into an interactive, personalized, two-way learning experience.

It provides a realistic AI video mentor that:
- Teaches concepts step-by-step
- Adapts explanations based on learner level
- Resolves doubts instantly (voice or text)
- Tracks progress and personalizes future lessons

Designed specifically for students and developers across India 🇮🇳

---

## 🎯 Problem Statement

Current learning platforms:
- Provide static, pre-recorded content
- Do not adapt to individual learners
- Lack real-time doubt resolution
- Are not optimized for rural accessibility

Learning is scalable, but not personalized.

---

## 💡 Our Solution

Bolt AI Tutor introduces:

- 🎥 Real-time AI-generated video teaching
- 🧠 Adaptive personalization engine
- 🎤 Voice-based doubt interaction
- 📊 Learning analytics dashboard
- 🌍 Scalable AWS-native cloud architecture

An AI mentor that teaches like a human and adapts like a coach.

---

## 🏗 System Architecture

The system follows a layered architecture:

User Layer  
→ Frontend (React / Flutter)  
→ Backend (FastAPI)  
→ AI Engine (Amazon Bedrock, Transcribe, Polly)  
→ Data Layer (DynamoDB, S3, CloudFront)

For detailed architecture, refer to `design.md`.

---

## 🛠 Tech Stack

### 🧠 AI Services
- Amazon Bedrock (LLM)
- Amazon Transcribe (Speech-to-Text)
- Amazon Polly (Text-to-Speech)

### ☁ Cloud
- AWS EC2
- AWS Lambda
- Amazon API Gateway
- Amazon CloudFront

### 💾 Database & Storage
- Amazon DynamoDB
- Amazon S3

### 🌐 Frontend
- React.js (Web)
- Flutter (Mobile)

### 🔐 Security
- AWS IAM
- JWT Authentication
- HTTPS Encryption

---

## 🔄 Core Features

- Smart onboarding & skill detection
- AI-generated dynamic lessons
- Realistic AI avatar video teaching
- Real-time doubt solving
- Adaptive difficulty adjustment
- Practice & quiz module
- Learning progress tracking
- Low-bandwidth support mode

---

## 📊 Estimated Cost (MVP)

₹12,000 – ₹15,000 per month (AWS-based)

Covered using AWS Hackathon Credits during development phase.

---

## 🚀 Getting Started (Development Setup)

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
