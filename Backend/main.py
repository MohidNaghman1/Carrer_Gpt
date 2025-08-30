# main.py
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# --- Now the rest of your imports can follow ---
from fastapi import FastAPI
from fastapi import FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import chat, auth
from fastapi.middleware.cors import CORSMiddleware # If you have CORS
from fastapi import FastAPI
from api.routes import chat, auth # Import the new auth router
from core.config import settings 

app = FastAPI(
    title="CareerGPT API",
    description="The backend API for the AI-Powered Career Intelligence Platform.",
    version="1.0.0"
)

origins = [
    settings.FRONTEND_ORIGIN,
    "http://localhost:3000", # For local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
# ------------------------------------

app.include_router(auth.router)
app.include_router(chat.router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the CareerGPT API"}
