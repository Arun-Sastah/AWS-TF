FROM python:3.11

WORKDIR /app

# Copy worker dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt redis rq python-dotenv boto3 asyncpg

# Copy worker code
COPY worker.py .

CMD ["python", "worker.py"]
