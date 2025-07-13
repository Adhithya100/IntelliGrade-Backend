from pydantic import BaseModel, EmailStr
from streamlit import status

class User(BaseModel):
    mail_id: EmailStr
    password: str
    
class Exam(BaseModel):
    exam_name: str
    subject: str
    max_marks: int
    exam_date: str
    
class AnswerKey(BaseModel):
    question_no: int
    question: str
    ideal_ans: str
    max_mark_per_q: int