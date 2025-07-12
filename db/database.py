import os
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

def create_supabase_client():
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)
    return supabase