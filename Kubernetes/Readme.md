# **Kubernetes Setup — Real-Time Financial Data Pipeline**

This document outlines the **production-style Kubernetes architecture** I used to deploy and orchestrate a **real-time financial data pipeline**.

---

# **Architecture Overview**

```text id="d8d3zw"
Kafka → Spark → S3 → Snowflake → dbt → Power BI
                     ↑
                  Airflow
                     ↑
               Kubernetes
                     ↑
        Prometheus → Grafana
```

---

# **Production Design Principles**

* I designed the system to be **decoupled**, where each component runs independently
* I used **namespace isolation** for better organization and security
* I implemented **on-demand processing**, where Spark and dbt run as jobs
* I centralized orchestration using **Airflow**
* I followed an **observability-first approach** by including monitoring

---

# **Namespace Strategy**

```text id="m5km74"
rtf-data-pipeline  → Application layer  
airflow            → Orchestration layer  
kafka              → Streaming layer  
monitoring         → Observability layer  
```

---

# **Prerequisites & Tool Installation**

Before starting, I installed the **required tools**.

---

## **Install Docker**

I downloaded and installed **Docker** from: [https://www.docker.com/](https://www.docker.com/)

Verify:

```bash id="1cfq4f"
docker --version
```

---

## **Install Minikube**

```bash id="0yxj2j"
choco install minikube
```

Verify:

```bash id="k4s6pk"
minikube version
```

---

## **Install kubectl**

```bash id="fbnzjb"
choco install kubernetes-cli
```

Verify:

```bash id="8m35yn"
kubectl version --client
```

---

## **Install Helm**

```bash id="4kws03"
choco install kubernetes-helm
```

Verify:

```bash id="8az2zl"
helm version
```

---

### **Why I used these tools**

* **Docker** to build container images
* **Minikube** to run a local Kubernetes cluster
* **kubectl** to interact with Kubernetes
* **Helm** to install complex applications like **Airflow, Kafka, and monitoring stacks**

---

# **STEP 1 — Start Kubernetes Cluster**

```bash id="32cdng"
minikube start --driver=docker --memory=8192 --cpus=4
kubectl get nodes
```

### **What I did**

I started a **local Kubernetes cluster**.

### **Why I did it**

To simulate a **real cloud environment** such as AWS EKS.

---

# **STEP 2 — Create Namespaces**

```bash id="m7huc2"
kubectl create namespace rtf-data-pipeline
kubectl create namespace airflow
kubectl create namespace kafka
kubectl create namespace monitoring
```

### **What I did**

I created **isolated environments** for each system.

### **Why I did it**

To improve **scalability, organization, and security**.

---

# **STEP 3 — Set Default Namespace (Optional but Pro Move)**

```bash
kubectl config set-context --current --namespace=rtf-data-pipeline
```

### **Why this is useful**

It is optional if you want you can use it because you don’t need to write `-n rtf-data-pipeline` every time.

---

# **STEP 4 — Deploy Application Layer**

### **Apply Configuration**

```bash id="vcv90u"
kubectl apply -f configmap.yaml -n rtf-data-pipeline
kubectl apply -f secret.yaml -n rtf-data-pipeline
```

### **What I did**

I loaded **configuration and secrets**.

### **Why I did it**

To separate **configuration from application code**.

---

### **Deploy Application**

```bash id="t37mqb"
kubectl apply -f deployment.yaml -n rtf-data-pipeline
```

### **What I did**

I created **application pods**.

### **Why I did it**

To ensure **automatic recovery, scaling, and high availability**.

---

### **Expose Application**

```bash id="hzyxlk"
kubectl apply -f service.yaml -n rtf-data-pipeline
minikube service rtf-service -n rtf-data-pipeline
```

### **What I did**

I exposed the **application**.

### **Why I did it**

To provide a **stable endpoint** since Pods have dynamic IPs.

---

# **STEP 5 — Deploy Airflow (Orchestration Layer)**

**Note:** first update DAG Synchronization (GitSync) in airflow-values.yaml then deploy Airflow scroll down for dag Synchronization information


```bash id="u7zdsv"
helm repo add apache-airflow https://airflow.apache.org
helm repo update

helm install airflow apache-airflow/airflow -n airflow --create-namespace -f airflow-values.yaml
```

* Here **-n** means namespace and **-f** means file; full names can also be used instead of shorthand.

---

### **Verify**

```bash id="xyjn18"
kubectl get pods -n airflow
```

---

### **Access UI**

***airflow-api-server***

```bash id="7zxte3"
kubectl port-forward svc/airflow-api-server 8080:8080 -n airflow
```
***airflow-webserver***
```bash id="7zxte3"
kubectl port-forward svc/airflow-webserver 8080:8080 -n airflow
```

Open: [http://localhost:8080](http://localhost:8080)

---

### **What I did**

I deployed **Airflow**.

### **Why I did it**

I used Airflow to **orchestrate pipelines, schedule tasks, and trigger Spark and dbt jobs**.

---

## **DAG Synchronization (GitSync)**

### **What I did**

I configured **GitSync** to automatically pull DAG files from my GitHub repository into Airflow.

### **Where I configured it**

Inside **airflow-values.yaml**.

### **How I configured it**

```yaml id="p0p6q3"
dags:
  gitSync:
    enabled: true
    repo: "https://github.com/Guruvendra47/real-time-financial-data-pipeline.git"
    branch: "main"
    subPath: "kubernetes/dags"
    wait: 60
    recommendedProbeSetting: true
```

### **When I use it**

I use this when I want **automatic DAG updates, version control for pipelines, and no manual file copying**.

### **Why I used it**

To ensure my **Airflow DAGs stay synced** with my GitHub repository in real time.

---

## **Create and Apply RBAC YAML**
SIMPLE EXPLANATION

- Airflow worker = a user inside Kubernetes
- That user is NOT allowed to manage pods in rtf-data-pipeline

- To fix this we have to give permission to airflow

We will create:

- Role → what actions allowed
- RoleBinding → who gets permission
  
**Airflow-rbac file**

```
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: airflow-role
  namespace: rtf-data-pipeline
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log", "events"]
    verbs: ["get", "list", "watch", "create", "delete", "patch", "update"]

---

apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: airflow-rolebinding
  namespace: rtf-data-pipeline
subjects:
  - kind: ServiceAccount
    name: airflow-worker
    namespace: airflow
roleRef:
  kind: Role
  name: airflow-role
  apiGroup: rbac.authorization.k8s.io
```
## **Apply**
```bash
kubectl apply -f airflow-rbac.yaml
```

**What this fixes**

Now Airflow can:

✔ Create pods
✔ Monitor pods
✔ Read logs
✔ Patch/update pods
✔ Read events

👉 Basically full lifecycle control

---
# **STEP 6 — Deploy Kafka (Streaming Layer)**

⚠️ I initially used Bitnami, but I switched to **Strimzi** for stability.

---

## **STEP 6.0 — Install Strimzi Operator**

```bash
kubectl apply -f https://strimzi.io/install/latest?namespace=kafka -n kafka
```
## **Verify**

```bash
kubectl get pods -n kafka
```
### **You should see:**
- strimzi-cluster-operator

Status → Running

---


## **STEP 6.1 — Create Kafka Cluster**

**Note:** If you using new version of Strimzi (0.46.0 or newer) which has deprecated the ZooKeeper and requires apply KafkaNodePools so apply Kafkanodepool before appling the kafka cluster:

**KafkaNodePool file**
```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaNodePool
metadata:
  name: rtf-pool
  namespace: kafka
  labels:
    strimzi.io/cluster: rtf-kafka
spec:
  replicas: 1   # ⚡ FIXED (not 3)
  roles:
    - controller
    - broker
  storage:
    type: ephemeral   # ⚡ FIXED
```
## **Apply**
```bash
kubectl apply -f kafka-node-pool.yaml -n kafka
```

**Kafka Cluster File**
```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: rtf-kafka
  namespace: kafka
spec:
  kafka:
    replicas: 1
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
    config:
      offsets.topic.replication.factor: 1
      transaction.state.log.replication.factor: 1
      transaction.state.log.min.isr: 1
    storage:
      type: ephemeral

  zookeeper:
    replicas: 1
    storage:
      type: ephemeral

  entityOperator:
    topicOperator: {}
    userOperator: {}
```

## **Apply**
```bash
kubectl apply -f kafka-cluster.yaml -n kafka
```
**Expected output**
```text
kafka.kafka.strimzi.io/rtf-kafka created
```

## **CHECK IF RESOURCE EXISTS**
```bash
kubectl get kafka -n kafka
```

**Expected output**
```text
rtf-kafka
```

## **Delete Duplicate file if exists**
```bash
kubectl delete kafka rtf-kafka-01 -n kafka
```

## **WATCH POD CREATION** 
```bash
kubectl get pods -n kafka -w
```

**After 1–2 minutes you should see:**
- rtf-kafka-kafka-0
- rtf-kafka-zookeeper-0

## **Why**

This creates:
* Kafka broker
* Zookeeper
* Internal networking
* Topic/user operators

## **Verify**

```bash
kubectl get pods -n kafka
```

### **You should see:**
- rtf-kafka-kafka-0
- rtf-kafka-zookeeper-0
- strimzi-cluster-operator

All → Status → Running

## **STEP 6.2 — Kafka Service (IMPORTANT FIX)**

Get Kafka Service
```bash
kubectl get svc -n kafka
```

**You will see something like:**
```
rtf-kafka-kafka-bootstrap   ClusterIP   ...   9092
```

**Your Kafka endpoint becomes:**
```
rtf-kafka-kafka-bootstrap.kafka.svc.cluster.local:9092
```


**Update your configmap.yaml, airflow-dag.py(spark code) files**

Your current config line:
```
KAFKA_BROKER: "kafka.kafka.svc.cluster.local:9092"
```

Open your configmap.yaml and Replace with:
```
KAFKA_BROKER: "rtf-kafka-kafka-bootstrap.kafka.svc.cluster.local:9092"
```

Your current airflow-dag line:

```
.option("kafka.bootstrap.servers", os.getenv("KAFKA_BROKER", "kafka:29092"))
```
Open your airflow-dag.py and Replace With:
```
.option("kafka.bootstrap.servers", os.getenv("KAFKA_BROKER", "rtf-kafka-kafka-bootstrap:9092"))
```

**Airflow DAG (Spark Code)**

Update your DAG:
```
spark_job = KubernetesPodOperator(
    task_id="spark_job",
    name="spark-job",
    namespace="rtf-data-pipeline",
    image="spark-job:7.0",
    cmds=["/opt/spark/bin/spark-submit"],
    arguments=["/opt/spark-app/spark-streaming-s3-aws.py"],
    env_vars={
        "KAFKA_BROKER": "rtf-kafka-kafka-bootstrap.kafka:9092",  # 🔥 FIXED
        "AWS_DEFAULT_REGION": "us-east-1",
        "S3_BUCKET": "real-time-financial-data-pipeline",
    },
    is_delete_operator_pod=True,
    get_logs=True,
)
```

**Apply update:**
```
kubectl apply -f configmap.yaml
kubectl rollout restart deployment rtf-app-deployment
```

---

## **STEP 6.3 — Create Kafka Topic**

**Kafka Topic File**
```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: trades
  namespace: kafka
  labels:
    strimzi.io/cluster: rtf-kafka
spec:
  partitions: 1
  replicas: 1
```

**Apply**
```bash
kubectl apply -f kafka-topic.yaml -n kafka
```

**Verify**
```bash
kubectl get kafkatopics -n kafka
```

**You should see:**
```text
trades
```
---

# **STEP 7 — Deploy Kafka Producer in kurbernetes(step-by-step)**

**STEP 1 — Create Dockerfile for Producer**
```Dockerfile
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
```
**STEP 2 — Build Image and import to minikube**
```bash
docker build -t kafka-producer:1.0 .
```
**Note:** if you want to build any other folder then **docker build -t kafka-producer:1.0 .\kafka**

```bash
minikube image load kafka-producer:1.0
```
**(or)**
**connect minikube to docker then build image**
* Connect Docker to Minikube
```bash
minikube docker-env | Invoke-Expression
```
* Build image INSIDE Minikube
```bash
docker build -t kafka-producer:1.0 .
```

**STEP 3 — Verify image**
```bash
docker images
```

**STEP 4 — Create Kubernetes Deployment**

**Producer-deployment File**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kafka-producer
  namespace: rtf-data-pipeline

spec:
  replicas: 1

  selector:
    matchLabels:
      app: kafka-producer

  template:
    metadata:
      labels:
        app: kafka-producer

    spec:
      containers:
        - name: kafka-producer
          image: kafka-producer:1.0
          imagePullPolicy: Never

          env:
            - name: KAFKA_BROKER
              value: "rtf-kafka-kafka-bootstrap.kafka:9092"

            - name: KAFKA_TOPIC
              value: "trades"

            - name: FINNHUB_API_KEY
              valueFrom:
                secretKeyRef:
                  name: rtf-secret
                  key: FINNHUB_API_KEY

            - name: SYMBOLS
              value: "AAPL,TSLA,MSFT,BINANCE:BTCUSDT"
```
**Note:** make sure in producer yaml file under env: you must use 
```
env:
- name: KAFKA_BROKER
  value: "rtf-kafka-kafka-bootstrap.kafka:9092"
```
for kafka name and value. 
you must not use: kafka:29092 ❌ localhost:9092 ❌ 
**why**
- kafka:29092 ❌ (Docker style)
- But Kubernetes uses:
```text
rtf-kafka-kafka-bootstrap.kafka:9092 ✅
```
so check you Yaml file if its in docker style change into kubernetes


**STEP 5 — Apply**

```bash
kubectl apply -f producer-deployment.yaml
```
**STEP 6 — Verify**
```bash
kubectl get pods -n rtf-data-pipeline
```

**Check Logs**
```bash
kubectl logs -l app=kafka-producer -n rtf-data-pipeline -f
```
**Delete Pod**
```bash
kubectl delete pod -l app=kafka-producer -n rtf-data-pipeline
```
### **What I did**

I deployed **Kafka Producer**.

### **Why I did it**

I used Kafka to enable **real-time streaming between systems**.

---

# **STEP 8 — Deploy Spark Execution Model in kurbernetes(step-by-step)**

**STEP 1 — Create Dockerfile for Producer**
```Dockerfile
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
```

**STEP 2 — Build Image and import to minikube**
```bash
docker build -t spark-job:1.0 .
```

**Note:** if you want to build any other folder then **docker build -t kafka-producer:1.0 .\kafka**

```bash
minikube image load spark-job:1.0
```
**(or)**
**connect minikube to docker then build image**
* Connect Docker to Minikube
```bash
minikube docker-env | Invoke-Expression
```
* Build image INSIDE Minikube
```bash
docker build -t spark-job:1.0 .
```

**STEP 5 — Verify image**
```bash
docker images
```

**Check Logs**
```bash
kubectl logs -l app=spark-job -n rtf-data-pipeline -f
```
**Delete Pod**
```bash
kubectl delete pod -l app=spark-job -n rtf-data-pipeline
```
### **Why I did it**

* **scalable distributed processing**
* **efficient resource usage**
* **runs only when needed**

---

# **STEP 9 — dbt Execution**

### **What I did**

I used **dbt** to transform data inside **Snowflake**.

### **How I implemented it**

* packaged as a **container**
* triggered by **Airflow**
* runs as a **Kubernetes pod**

### **Why I did it**

To ensure **modular and repeatable transformations**.

---

# **STEP 10 — Monitoring Setup**

```bash id="9s7k3q"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --create-namespace
```

---

### **Access Grafana**

```bash id="sv9n4l"
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring
```

---

### **What I did**

I deployed **monitoring tools**.

### **Why I did it**

To **monitor system health, track performance, and detect failures**.

---

# **STEP 10 — Run the Pipeline**

Inside **Airflow UI**:

1. I enable the **DAG**
2. I trigger the **run**
3. I monitor **execution**

---

### **Execution Flow**

```text id="rsc22l"
Airflow → Spark pod → S3 → dbt → analytics output
```

---

# **Cleanup**

```bash id="y3pqlm"
helm uninstall airflow -n airflow
helm uninstall kafka -n kafka
kubectl delete namespace airflow kafka monitoring rtf-data-pipeline
minikube delete
```

---

# **Key Takeaways**

* I used **Kubernetes** to separate systems into independent layers
* I used **Airflow** to orchestrate workflows
* I ran **Spark and dbt on demand**
* I used **Kafka for streaming**
* I implemented **monitoring to ensure reliability**

---

# **Author**

**Guruvendra Singh**
