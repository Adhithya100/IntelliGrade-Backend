from pydantic import BaseModel, EmailStr

class User(BaseModel):
    mail_id: EmailStr
    password: str