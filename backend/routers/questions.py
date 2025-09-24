from fastapi import APIRouter, HTTPException, Depends, Header
from models import AskModel, AnswerResponse, QuizAnswerModel
from services.ai_service import generate_answer, generate_quiz
from database import db
from bson import ObjectId
from datetime import datetime, timedelta
import uuid

router = APIRouter()

def ensure_obj_id(doc):
    doc["_id"] = str(doc["_id"])
    return doc

@router.post("/ask", response_model=AnswerResponse)
async def ask_question(payload: AskModel, authorization: str | None = Header(None)):
    """
    payload: { user_id, subject, query }
    returns: answer, quiz object and quiz_id
    """
    # 1) Generate answer
    answer = generate_answer(payload.query, payload.subject)

    # 2) Generate quiz (try to create JSON)
    quiz = generate_quiz(payload.query, payload.subject)
    quiz_id = str(uuid.uuid4())

    # 3) Create document and insert into MongoDB
    doc = {
        "user_id": payload.user_id,
        "subject": payload.subject,
        "doubt": payload.query,
        "answer": answer,
        "quiz": quiz,
        "quiz_id": quiz_id,
        "user_choice": None,
        "is_correct": None,
        "created_at": datetime.utcnow(),
        # expires_at is just informational; frontend controls the 15s timer
        "expires_at": datetime.utcnow() + timedelta(seconds=15)
    }
    await db["progress"].insert_one(doc)

    return {"response": answer, "quiz_id": quiz_id, "quiz": quiz}

@router.post("/quiz/answer")
async def submit_quiz_answer(payload: QuizAnswerModel):
    # find the quiz by quiz_id
    doc = await db["progress"].find_one({"quiz_id": payload.quiz_id, "user_id": payload.user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Quiz not found")
    # if already answered
    if doc.get("user_choice") is not None:
        raise HTTPException(status_code=400, detail="Quiz already answered")

    correct = doc["quiz"].get("correct")
    is_correct = (payload.user_choice == correct)

    update = {
        "$set": {
            "user_choice": payload.user_choice,
            "is_correct": is_correct,
            "answered_at": datetime.utcnow()
        }
    }
    await db["progress"].update_one({"_id": doc["_id"]}, update)

    # Optionally, update user stats collection (simple increment)
    stat_key = {"user_id": payload.user_id, "subject": doc["subject"], "topic": doc["doubt"][:50]}
    await db["stats"].update_one(
        {"user_id": payload.user_id, "subject": doc["subject"]},
        {"$inc": {"attempts": 1, "correct": 1 if is_correct else 0}},
        upsert=True
    )

    return {"quiz_id": payload.quiz_id, "is_correct": is_correct}
