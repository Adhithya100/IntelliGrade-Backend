from fastapi import FastAPI, Depends, Response
from models import User
from db.database import create_supabase_client
from auth import get_current_user

app = FastAPI()

supabase = create_supabase_client()

@app.get("/")
async def root():
    return {"message":"testing"}

@app.post("/signup")
async def signup(user: User):
    try:
        response = supabase.auth.sign_up({"email": user.mail_id, "password": user.password})
        
        return {"message": "User created successfully", "user": response}

    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}

@app.post("/signin")
async def signin(user: User, res: Response):
    try:
        response = supabase.auth.sign_in_with_password({"email": user.mail_id, "password": user.password})
        
        access_token = response.session.access_token
        
        res.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True
        )
        
        return {"message": "User signed in successfully", "user": response}

    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}
    
@app.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    return {"message": "This is a protected route", "user": user}

