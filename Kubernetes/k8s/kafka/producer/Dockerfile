FROM python:3.11-slim

# Prevent log buffering (important for kubectl logs)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy files
COPY kafka-producer.py .
COPY configs/ configs/

# Install dependencies
RUN pip install --no-cache-dir \
    kafka-python-ng \
    pyyaml

# Run producer
CMD ["python", "kafka-producer.py"]