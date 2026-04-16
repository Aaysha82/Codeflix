
from celery import Celery
import os

REDIS_URL = "sqla+sqlite:///BACKEND/celery_broker.db"
try:
    app = Celery("test", broker=REDIS_URL)
    print("Celery app initialized")
    # This might not trigger the error until we actually try to use it
    from kombu import Connection
    conn = Connection(REDIS_URL)
    print(f"Connection created: {conn.transport_cls}")
    conn.connect()
    print("Connected!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
