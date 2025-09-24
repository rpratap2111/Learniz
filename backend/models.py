from pydantic import BaseModel, EmailStr
from typing import List, Optional

class SignupModel(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginModel(BaseModel):
    email: EmailStr
    password: str

class AskModel(BaseModel):
    user_id: str
    subject: str 
    query: str

class QuizAnswerModel(BaseModel):
    quiz_id: str
    user_id: str
    user_choice: str

class AnswerResponse(BaseModel):
    response: str
    quiz_id: str
    quiz: dict
