"""
BACKEND/celery_app.py
Celery configuration for asynchronous AML processing.
"""
import os
from celery import Celery

# Use a local SQLite database for the demo since Redis is missing
# In production, swap back to Redis: REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_URL = "sqla+sqlite:///BACKEND/celery_broker.db"

celery_app = Celery(
    "proofsar_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["BACKEND.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600, # 1 hour max
)
