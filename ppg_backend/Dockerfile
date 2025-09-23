# ppg_backend Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
# Install dependencies using uv only
RUN pip install uv && uv pip install --system -r requirements.txt

# Copy source code
COPY app/ ./app/
COPY main.py .

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
