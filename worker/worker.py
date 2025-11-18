# worker.py
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# -----------------------------
# Fix Python path so "app.*" works
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Import your job function (backend code)
from app.jobs.jobs import create_server_job_sync

# -----------------------------
# Redis Connection
# -----------------------------
from redis import Redis
from rq import Worker, Queue

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Create Redis client
redis_conn = Redis.from_url(REDIS_URL)

# Setup queue
queue = Queue("default", connection=redis_conn)

# -----------------------------
# Worker Start
# -----------------------------
if __name__ == "__main__":
    print("🚀 RQ Worker Started and Listening on Queue: default")

    # Create and start the worker
    worker = Worker([queue], connection=redis_conn)

    # Start processing tasks
    worker.work()
