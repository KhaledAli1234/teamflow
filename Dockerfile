# Build stage
FROM python:3.10-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final runtime stage
FROM python:3.10-slim

WORKDIR /app

# Create a non-root system user
RUN groupadd -r teamflow && useradd -r -g teamflow -d /app teamflow

COPY --from=builder /root/.local /home/teamflow/.local
COPY --chown=teamflow:teamflow . .

ENV PATH=/home/teamflow/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

USER teamflow

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
