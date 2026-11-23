FROM python:3.12-slim
WORKDIR /app
# Phase 0 stub – replace in Phase 1
RUN pip install fastapi uvicorn httpx --no-cache-dir
COPY . .
# Minimal health endpoint so docker-compose healthcheck passes
CMD ["python", "-c", "import uvicorn; from fastapi import FastAPI; app = FastAPI(); app.get('/health')(lambda: {'status': 'stub'}); uvicorn.run(app, host='0.0.0.0', port=8001)"]
