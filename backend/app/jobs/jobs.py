# jobs.py
import os
import asyncio
import logging
from datetime import datetime

from app.services.terraform_utils import (
    generate_root_terraform_files,
    run_terraform_commands,
)
from app.services.db_utils import log_request, log_resource

logger = logging.getLogger(__name__)

# Get backend root path for terraform templates
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TERRAFORM_ROOT = os.path.join(BACKEND_DIR, "terraform_templates")


# ----------------------------------------------------------------------
# Async job (RQ CANNOT run this directly)
# ----------------------------------------------------------------------
async def create_server_job(device_id: str, instance_name: str, user: str) -> dict:
    """
    Steps:
     1. Normalize device_id
     2. Create terraform working folder
     3. Run terraform init/apply
     4. Log results to DB and Redis
    """

    # Convert device_id to numeric for DB request_id
    try:
        request_id = int(device_id)
    except:
        request_id = abs(hash(device_id)) % (10 ** 8)

    # Terraform path → backend/terraform_templates/<device_id>
    device_path = os.path.join(TERRAFORM_ROOT, device_id)

    logger.info(f"🚀 Job started for device_id={device_id}, path={device_path}")

    # Log start
    log_id = await log_request(
        request_id=request_id,
        user_id=user,
        status="create_started"
    )

    try:
        # Generate terraform files
        generate_root_terraform_files(
            device_id=device_id,
            instance_name=instance_name,
            path=device_path
        )

        # Run Terraform
        success, output, duration = await run_terraform_commands(
            path=device_path,
            device_id=str(device_id),
            instance_name=instance_name
        )

        # Record final status
        await log_request(
            request_id=request_id,
            user_id=user,
            status="success" if success else "failed",
            duration_seconds=duration,
            error_message=None if success else output
        )

        # Log resource if successful
        if success:
            await log_resource(
                log_id=log_id,
                resource_type="EC2",
                resource_name=instance_name,
                resource_id_value=device_id
            )

        return {
            "success": success,
            "output": output,
            "duration": duration
        }

    except Exception as e:
        error_text = f"Unhandled error: {str(e)}"
        logger.error(error_text)

        await log_request(
            request_id=request_id,
            user_id=user,
            status="error",
            error_message=error_text
        )

        return {
            "success": False,
            "output": error_text,
            "duration": 0
        }


# ----------------------------------------------------------------------
# RQ requires a SYNC function → wrapper for async job
# ----------------------------------------------------------------------
def create_server_job_sync(device_id: str, instance_name: str, user: str) -> dict:
    """
    This wrapper allows RQ (sync) to run async workflows.
    RQ will execute THIS function.
    """
    try:
        return asyncio.run(
            create_server_job(device_id, instance_name, user)
        )
    except RuntimeError:
        # If event loop exists (rare in worker), create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            create_server_job(device_id, instance_name, user)
        )
