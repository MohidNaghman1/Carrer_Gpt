# db/models.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime

from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    # ADD LENGTH HERE
    email = Column(String(255), unique=True, index=True, nullable=False)
    # ADD LENGTH HERE
    hashed_password = Column(String(255), nullable=False)
    
    chat_sessions = relationship("ChatSession", back_populates="owner")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    # ADD LENGTH HERE
    title = Column(String(255), index=True, default="New Chat Session")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resume_text = Column(Text, nullable=True)
    
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="chat_sessions")
    
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    # ADD LENGTH HERE
    role = Column(String(255), nullable=False) # "human" or "ai"
    content = Column(Text, nullable=False) # Text doesn't need a length
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    session = relationship("ChatSession", back_populates="messages")