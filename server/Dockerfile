# AgentLens server — FastAPI + SQLite
FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Data directory for SQLite
RUN mkdir -p /data

ENV AGENTLENS_DB_PATH=/data/agentlens.db
ENV PYTHONUNBUFFERED=1

EXPOSE 8766

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8766"]
