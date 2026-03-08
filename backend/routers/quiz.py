from fastapi import APIRouter, HTTPException
from models import QuizRequest, QuizResponse
from services.bedrock_service import get_quiz

router = APIRouter()

@router.post("/quiz", response_model=QuizResponse)
async def quiz(req: QuizRequest):
    try:
        questions = get_quiz(req.topic, req.skill_level, req.num_questions)
        return QuizResponse(questions=questions, topic=req.topic)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
