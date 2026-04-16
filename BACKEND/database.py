"""
BACKEND/database.py
SQLAlchemy database configuration for persistent storage.
Supports PostgreSQL (production) and SQLite (development fallback).
"""
import os
from sqlalchemy import create_engine, Column, String, Float, Boolean, DateTime, JSON, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./DATA/proofsar.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ─── Models ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="analyst")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True)
    seq = Column(Integer)
    event_type = Column(String, index=True)
    actor = Column(String, index=True)
    timestamp = Column(String)  # Store as ISO string for bit-perfect hashing
    event_data = Column(JSON)
    prev_hash = Column(String)
    current_hash = Column(String)

class TransactionRecord(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    account_id = Column(String, index=True)
    amount = Column(Float)
    location = Column(String)
    channel = Column(String)
    currency = Column(String)
    risk_score = Column(Float)
    risk_level = Column(String)
    is_suspicious = Column(Boolean)
    detected_at = Column(DateTime, default=datetime.now(timezone.utc))

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
