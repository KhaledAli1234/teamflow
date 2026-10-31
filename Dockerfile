# Build stage
FROM python:3.10-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 --retries 5 --prefix=/install -r requirements.txt

# Final runtime stage
FROM python:3.10-slim

WORKDIR /app

# Create a non-root system user
RUN groupadd -r teamflow && useradd -r -g teamflow -d /app teamflow

COPY --from=builder /install /usr/local
COPY --chown=teamflow:teamflow . .

ENV PYTHONUNBUFFERED=1

USER teamflow

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]