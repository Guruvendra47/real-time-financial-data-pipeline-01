# ==========================================
# BASE IMAGE
# ==========================================
FROM apache/spark:3.5.1

USER root

WORKDIR /opt/spark-app

RUN mkdir -p /opt/spark-app/configs

# ==========================================
# COPY APPLICATION FILES (FIXED FILENAME)
# ==========================================
COPY spark-streaming-s3-aws.py /opt/spark-app/spark-streaming-s3-aws.py
COPY configs/ configs

# ==========================================
# INSTALL PYTHON DEPENDENCIES
# ==========================================
RUN pip install --no-cache-dir boto3 pandas pyyaml

# ==========================================
# FIXED COMPLETE DEPENDENCIES
# ==========================================
RUN mkdir -p /opt/spark/jars && \
    curl -L -o /opt/spark/jars/spark-sql-kafka-0-10_2.12-3.5.1.jar \
    https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.1/spark-sql-kafka-0-10_2.12-3.5.1.jar && \
    curl -L -o /opt/spark/jars/spark-token-provider-kafka-0-10_2.12-3.5.1.jar \
    https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.1/spark-token-provider-kafka-0-10_2.12-3.5.1.jar && \
    curl -L -o /opt/spark/jars/kafka-clients-3.5.1.jar \
    https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.5.1/kafka-clients-3.5.1.jar && \
    curl -L -o /opt/spark/jars/commons-pool2-2.11.1.jar \
    https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar && \
    curl -L -o /opt/spark/jars/hadoop-aws-3.3.4.jar \
    https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    curl -L -o /opt/spark/jars/aws-java-sdk-bundle-1.12.262.jar \
    https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar
    
ENV PYTHONUNBUFFERED=1

CMD ["/opt/spark/bin/spark-submit", "/opt/spark-app/spark-streaming-s3-aws.py"]
