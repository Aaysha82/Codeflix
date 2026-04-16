"""
BACKEND/celery_app.py
Celery configuration for asynchronous AML processing.
"""
import os
from celery import Celery

# Local SQLite broker (for demo/dev)
BROKER_URL  = "sqla+sqlite:///BACKEND/celery_broker.db"
RESULTS_URL = "db+sqlite:///BACKEND/celery_broker.db"

celery_app = Celery(
    "proofsar_tasks",
    broker=BROKER_URL,
    backend=RESULTS_URL,
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
