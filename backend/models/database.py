from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv

load_dotenv('../.env')

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Municipality(Base):
    __tablename__ = "municipalities"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    domain = Column(String, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversations = relationship("Conversation", back_populates="municipality")
    documents = relationship("Document", back_populates="municipality")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    municipality_id = Column(String, ForeignKey("municipalities.id"))
    session_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    municipality = relationship("Municipality", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(Text)  # JSON string of sources
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    municipality_id = Column(String, ForeignKey("municipalities.id"))
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    category = Column(String, default="fiscal")
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    municipality = relationship("Municipality", back_populates="documents")

# Funcție pentru a crea tabelele
def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
