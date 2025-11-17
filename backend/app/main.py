# main.py
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Ensure project root is importable
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from redis import Redis
from rq import Queue
from rq.job import Job

from app.models.request_models import DeployRequest
from app.jobs.jobs import create_server_job_sync
from app.services.db_utils import init_db

# -------------------------------------------------------------------
# FastAPI initialization
# -------------------------------------------------------------------
app = FastAPI(title="Terraform Provisioner")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# Redis connection (from .env)
# -------------------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_conn = Redis.from_url(REDIS_URL)
task_queue = Queue(connection=redis_conn)

# -------------------------------------------------------------------
# Startup event → Initialize PostgreSQL tables
# -------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    await init_db()

# -------------------------------------------------------------------
# API endpoint to enqueue Terraform job
# -------------------------------------------------------------------
@app.post("/create-server")
async def create_server(request: DeployRequest):
    """
    Enqueue the synchronous wrapper since RQ cannot run async functions directly.
    """
    job = task_queue.enqueue(
        create_server_job_sync,
        request.device_id,
        request.instance_name,
        request.user
    )
    return {"message": "Deployment started", "job_id": job.id}

# -------------------------------------------------------------------
# API endpoint to check job status
# -------------------------------------------------------------------
@app.get("/job/{job_id}")
async def job_status(job_id: str):
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        return {"status": "not_found", "result": None}

    return {
        "status": job.get_status(),
        "result": job.result
    }
