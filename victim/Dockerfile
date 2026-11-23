FROM python:3.12-slim

# Why slim? Keeps the image small. We don't need compilers — all deps are
# pure Python or have pre-built wheels.
WORKDIR /app

# Install deps first (separate layer so rebuilds are fast when only code changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Non-root user for security hygiene
RUN adduser --disabled-password --gecos "" sentinel
USER sentinel

EXPOSE 8001

# uvicorn with 1 worker — single-threaded is fine for a demo/test target.
# --no-access-log keeps output clean; our app does its own logging.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--no-access-log"]
