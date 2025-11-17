# worker.py
import os
import sys
from dotenv import load_dotenv

import redis
from rq import Worker, Queue, Connection

# Load environment variables from .env
load_dotenv()

# Fix import path so "app.*" works in Docker & EC2
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.jobs.jobs import create_server_job_sync

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_conn = redis.from_url(REDIS_URL)

# Listen to the default queue
queue_list = ["default"]
queues = [Queue(name, connection=redis_conn) for name in queue_list]

if __name__ == "__main__":
    print("🚀 RQ Worker Started...")
    with Connection(redis_conn):
        worker = Worker(queues)
        worker.work()
