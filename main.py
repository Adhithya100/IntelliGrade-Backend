# Import necessary libraries
from fastapi import FastAPI, Depends, Response, Request, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from db.database import create_supabase_client
from typing import List
from google import genai
from models import User, Exam, AnswerKey, StudentDetail
from pdf2image import convert_from_bytes
from dotenv import load_dotenv
import json
import os

# Load environment variables
load_dotenv()
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_KEY")
GEMINI_API_KEY= os.getenv("GEMINI_API_KEY")

# Initialize clients
app = FastAPI()
supabase = create_supabase_client()
gemini = genai.Client(api_key=GEMINI_API_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Function to get the current authenticated user
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

# Function to upload answer key to the database
def upload_answer_key_to_db(images, exam_id):
    response = gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=[images, "Generate a json in the given format using the images. I want the text as it is from the images, do not add/replace/remove content."],
        config={
            "response_mime_type": "application/json",
            "response_schema": list[AnswerKey],
        },
    )
    
    for i in response.to_json_dict()['parsed']:
        i['exam_id'] = exam_id
        supabase.from_("answer_keys").insert(i).execute()

def process_student_submission(images, exam_id, user_id):
    response = gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=[images, "Generate a json in the given format using the images. Take only the needed information from the images like name, roll no, class and section."],
        config={
            "response_mime_type": "application/json",
            "response_schema": StudentDetail,
        },
    )
    data=json.loads(response.text)
    data['user_id']=user_id
    supabase.from_("students").insert(data).execute()

#API Endpoints
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
    
@app.get("/protected") # Example of a protected route
async def protected_route(user: dict = Depends(get_current_user)):
    return {"message": "This is a protected route", "user": user}

@app.post("/add_exam")
async def add_exam(exam: Exam, res: Response, user: dict = Depends(get_current_user)):
    try:
        data = {
            "user_id": user.user.id,
            "exam_name": exam.exam_name,
            "subject": exam.subject,
            "max_marks": exam.max_marks,
            "exam_date": exam.exam_date,
        }
        
        response = supabase.from_("exams").insert(data).execute()
        
        exam_id = response.data[0]['exam_id']
        res.set_cookie(
            key="exam_id",
            value=exam_id,
            httponly=True
        )
        
        return {"message": "Exam added successfully", "exam": response.data}
    
    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}
    
@app.post("/upload_answer_key")
async def upload_answer_key(res: Response, req: Request, file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    try:
        exam_id = req.cookies.get("exam_id")
        res.delete_cookie(key="exam_id")
        
        contents = await file.read()
        images = convert_from_bytes(contents)
        
        upload_answer_key_to_db(images, exam_id)
            
        return {"message": "Answer key uploaded successfully", "exam_id": exam_id}
    
    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}
    
@app.get("/get_user")
async def get_user(user: dict = Depends(get_current_user)):
    return {"user": user}

@app.get("/get_exams")
async def get_exams(user: dict = Depends(get_current_user)):
    response = supabase.table("exams").select("*").eq("user_id", user.user.id).execute()
    return {"exams": response.data}

@app.post("/upload_answer_scripts")
async def upload_answer_scripts(res: Response, req: Request, files: List[UploadFile] = File(...), user: dict = Depends(get_current_user), exam_id: str = None):
    processed_students = []
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")
    for file in files:
        try:
            contents = await file.read()
            images=convert_from_bytes(contents)
            student_info = process_student_submission(images, exam_id, user.user.id)
            processed_students.append(student_info)

        except Exception as e:
            # Log the error but continue processing other files
            print(f"Failed to process file {file.filename}: {str(e)}")