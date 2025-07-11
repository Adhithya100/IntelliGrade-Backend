from fastapi import Request, HTTPException
import jwt
import os
from dotenv import load_dotenv
import base64

load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_KEY")

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated (no cookie)")

    try:
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
        return payload
    
    except Exception as e:
        print(f"JWT Error: {e}")
        raise HTTPException(status_code=401, detail=f"Token error: {str(e)}")
