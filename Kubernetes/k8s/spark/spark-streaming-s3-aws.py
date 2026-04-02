# ==========================================
# spark-streaming-s3-aws.py (FINAL - FIXED)
# ==========================================

import os
import yaml

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, from_unixtime, window, avg, sum, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType

# ==========================================
# 1. LOAD CONFIG
# ==========================================
CONFIG_PATH = "configs/spark_config.yaml"

if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")

with open(CONFIG_PATH, "r") as file:
    config = yaml.safe_load(file)

APP_NAME = config.get("app_name", "spark-streaming-app")

# Store checkpoints in S3 (important for K8s restart safety)
CHECKPOINT_BASE = config.get(
    "checkpoint_location",
    "s3a://real-time-financial-data-pipeline/checkpoints"
)

# ==========================================
# 2. READ ENV VARIABLES (FROM AIRFLOW / K8S)
# ==========================================
aws_access_key = os.getenv("AWS_ACCESS_KEY")
aws_secret_key = os.getenv("AWS_SECRET_KEY")
aws_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
bucket_name = os.getenv("S3_BUCKET", "real-time-financial-data-pipeline")

kafka_broker = os.getenv("KAFKA_BROKER")

# STRICT VALIDATION (IMPORTANT)
if not kafka_broker:
    raise ValueError("❌ KAFKA_BROKER not set in environment")

if not aws_access_key or not aws_secret_key:
    raise ValueError("❌ AWS credentials missing")

# ==========================================
# 3. CREATE SPARK SESSION
# ==========================================
spark = (
    SparkSession.builder
    .appName(APP_NAME)
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

# ==========================================
# 4. S3 CONFIGURATION
# ==========================================
hadoop_conf = spark._jsc.hadoopConfiguration()

hadoop_conf.set("fs.s3a.access.key", aws_access_key)
hadoop_conf.set("fs.s3a.secret.key", aws_secret_key)
hadoop_conf.set("fs.s3a.endpoint", f"s3.{aws_region}.amazonaws.com")
hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")

# ==========================================
# 5. DEFINE SCHEMA
# ==========================================
schema = StructType([
    StructField("p", DoubleType()),
    StructField("s", StringType()),
    StructField("t", LongType()),
    StructField("v", DoubleType())
])

# ==========================================
# 6. READ STREAM FROM KAFKA
# ==========================================
kafka_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", kafka_broker)
    .option("subscribe", "trades")
    .option("startingOffsets", "latest")
    .option("failOnDataLoss", "false")
    .load()
)

# ==========================================
# 7. TRANSFORM DATA
# ==========================================
clean_df = (
    kafka_df
    .selectExpr("CAST(value AS STRING)")
    .select(from_json(col("value"), schema).alias("data"))
    .select("data.*")
    .select(
        col("p").alias("price"),
        col("s").alias("symbol"),
        to_timestamp(from_unixtime(col("t") / 1000)).alias("timestamp"),
        col("v").alias("volume")
    )
)

# ==========================================
# 8. DEBUG (IMPORTANT - SEE DATA)
# ==========================================
console_query = (
    clean_df.writeStream
    .format("console")
    .outputMode("append")
    .start()
)

# ==========================================
# 9. BRONZE LAYER
# ==========================================
raw_query = (
    clean_df.writeStream
    .format("parquet")
    .option("path", f"s3a://{bucket_name}/raw/trades/")
    .option("checkpointLocation", f"{CHECKPOINT_BASE}/raw/")
    .outputMode("append")
    .start()
)

# ==========================================
# 10. SILVER LAYER
# ==========================================
processed_df = clean_df.filter(
    col("price").isNotNull() &
    col("symbol").isNotNull() &
    col("timestamp").isNotNull() &
    col("volume").isNotNull()
)

silver_query = (
    processed_df.writeStream
    .format("parquet")
    .option("path", f"s3a://{bucket_name}/processed/trades/")
    .option("checkpointLocation", f"{CHECKPOINT_BASE}/processed/")
    .outputMode("append")
    .start()
)

# ==========================================
# 11. GOLD LAYER
# ==========================================
gold_df = (
    processed_df
    .withWatermark("timestamp", "1 minute")
    .groupBy(
        window(col("timestamp"), "1 minute"),
        col("symbol")
    )
    .agg(
        avg("price").alias("avg_price"),
        sum("volume").alias("total_volume")
    )
)

gold_query = (
    gold_df.writeStream
    .format("parquet")
    .option("path", f"s3a://{bucket_name}/curated/trades/")
    .option("checkpointLocation", f"{CHECKPOINT_BASE}/curated/")
    .outputMode("append")
    .start()
)

# ==========================================
# 12. KEEP STREAM RUNNING
# ==========================================
spark.streams.awaitAnyTermination()