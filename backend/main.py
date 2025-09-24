# main.py
from fastapi import FastAPI
from routers import questions, progress
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Learniz API")

origins = ["*"]  # change in prod to your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(questions.router, prefix="/api")
app.include_router(progress.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Learniz API running"}
