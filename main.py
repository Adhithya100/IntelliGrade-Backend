from fastapi import FastAPI, Depends, Response, Request, HTTPException
from models import User
import os
from dotenv import load_dotenv
from db.database import create_supabase_client

load_dotenv()
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_KEY")

app = FastAPI()
supabase = create_supabase_client()

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated (no cookie)")

    try:
        payload = supabase.auth.get_user(token)
        return payload
    
    except Exception as e:
        print(f"JWT Error: {e}")
        raise HTTPException(status_code=401, detail=f"Token error: {str(e)}")

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
    
@app.get("/signout")
async def signout(res: Response, user: dict = Depends(get_current_user)):
    try:
        response = supabase.auth.sign_out()
        res.delete_cookie(key="access_token")
        return {"message": "signed out", "user": response}

    except Exception as e:
        return {"message": f"An error occured: {str(e)}"}
    
@app.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    return {"message": "This is a protected route", "user": user}

