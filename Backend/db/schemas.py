# db/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

# --- Message Schemas ---
class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    session_id: int
    role: str # "human" or "ai"
    timestamp: datetime.datetime

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime.datetime: lambda v: v.isoformat()
        }
    }

# --- Chat Session Schemas ---
class ChatSessionBase(BaseModel):
    title: str = Field(default="New Chat Session")

class ChatSessionCreate(ChatSessionBase):
    # ADD THIS OPTIONAL FIELD
    first_message: Optional[str] = None

class ChatSessionUpdate(BaseModel):
    title: str


class ChatSession(ChatSessionBase):
    id: int
    user_id: int # We'll fake this for now
    created_at: datetime.datetime
    messages: List[Message] = []

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime.datetime: lambda v: v.isoformat()
        }
    }

# --- User & Token Schemas (for later) ---
# It's good practice to define them now.

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None