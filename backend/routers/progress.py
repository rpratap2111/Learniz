# routers/progress.py
from fastapi import APIRouter
from database import db

router = APIRouter()

@router.get("/progress/{user_id}")
async def get_progress(user_id: str, subject: str | None = None):
    query = {"user_id": user_id}
    if subject:
        query["subject"] = subject
    cursor = db["progress"].find(query).sort("created_at", -1).limit(200)
    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results

@router.get("/stats/{user_id}")
async def get_stats(user_id: str):
    # return aggregated stats per subject
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$subject", "attempts": {"$sum": 1}, "correct": {"$sum": {"$cond": ["$is_correct", 1, 0]}}}}
    ]
    res = await db["progress"].aggregate(pipeline).to_list(length=20)
    return res
