# Multi-stage build for minimal image size
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY ./src ./src
COPY ./requirements.txt .

# Create runtime directories for uploads, logs, and audit chains
RUN mkdir -p /app/data/uploads /app/data/logs /app/data/audit /app/data/outputs

EXPOSE 8000
# Run the FastAPI server via the unified main.py entrypoint
CMD ["python", "src/main.py", "--server", "--host", "0.0.0.0", "--port", "8000"]
