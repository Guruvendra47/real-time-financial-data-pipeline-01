# ==========================================
# kafka-producer.py (FINAL - CLEAN & STABLE)
# ==========================================

import os
import json
import time
import logging
import yaml
from kafka import KafkaProducer

# ==========================================
# LOGGING (important for kubectl logs)
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ==========================================
# LOAD CONFIG
# ==========================================
CONFIG_PATH = "configs/kafka_config.yaml"

if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"Missing config file: {CONFIG_PATH}")

with open(CONFIG_PATH, "r") as file:
    config = yaml.safe_load(file)

TOPIC = config.get("topic", "trades")

# ==========================================
# ENV VARIABLES (KUBERNETES)
# ==========================================
KAFKA_BROKER = os.getenv("KAFKA_BROKER")

if not KAFKA_BROKER:
    raise ValueError("❌ KAFKA_BROKER not set in environment")

# ==========================================
# CREATE KAFKA PRODUCER
# ==========================================
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    retries=5,
    linger_ms=10,
    acks="all"
)

logging.info(f"Connected to Kafka broker: {KAFKA_BROKER}")
logging.info(f"Using topic: {TOPIC}")

# ==========================================
# DATA GENERATOR
# ==========================================
def generate_data():
    return {
        "p": 100.5,                     # price
        "s": "AAPL",                    # symbol
        "t": int(time.time() * 1000),   # timestamp (ms)
        "v": 10.0                       # volume
    }

# ==========================================
# SEND LOOP
# ==========================================
while True:
    try:
        data = generate_data()

        logging.info(f"Sending: {data}")

        producer.send(TOPIC, value=data)
        producer.flush()

        time.sleep(2)

    except Exception as e:
        logging.error(f"Producer error: {e}")
        time.sleep(5)