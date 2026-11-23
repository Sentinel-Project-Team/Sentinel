FROM python:3.12-slim
WORKDIR /app
RUN pip install fastapi uvicorn --no-cache-dir
COPY . .
CMD ["python", "-c", "import uvicorn; from fastapi import FastAPI; app = FastAPI(); app.get('/health')(lambda: {'status': 'stub'}); uvicorn.run(app, host='0.0.0.0', port=8080)"]
