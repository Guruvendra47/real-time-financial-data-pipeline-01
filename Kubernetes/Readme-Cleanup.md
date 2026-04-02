# 🧹 Kubernetes Cleanup Guide

A simple and clear guide to clean your Kubernetes environment — from partial cleanup to full reset.

---

## 📌 Overview

When working with Kubernetes, you may need to delete resources for:

* restarting your project
* fixing broken deployments
* cleaning unused resources

This guide provides **3 levels of cleanup** depending on your need.

---

## ⚠️ Important

Choose the correct level carefully:

| Level         | Type             | Impact                    |
| ------------- | ---------------- | ------------------------- |
| 🟢 Safe       | Project Cleanup  | Deletes only your project |
| 🟡 Medium     | Helm + Namespace | Removes apps completely   |
| 🔴 Full Reset | Cluster Reset    | Deletes EVERYTHING        |

---

# 🟢 Option 1 — Safe Cleanup (Recommended)

Delete only your project namespaces.

```bash
kubectl delete namespace airflow
kubectl delete namespace monitoring
kubectl delete namespace rtf-data-pipline
```

### ✅ Removes:

* Airflow
* Prometheus & Grafana
* Data pipeline resources

### ❌ Keeps:

* Kubernetes cluster
* System components

👉 Best for daily development cleanup.

---

# 🟡 Option 2 — Helm Cleanup (Clean Uninstall)

First uninstall Helm releases:

```bash
helm uninstall airflow -n airflow
helm uninstall monitoring -n monitoring
```

Then delete namespaces:

```bash
kubectl delete namespace airflow
kubectl delete namespace monitoring
kubectl delete namespace rtf-data-pipline
```

### ✅ Removes:

* Helm-managed applications
* All related resources

👉 Best when you want a **clean reinstall**.

---

# 🔴 Option 3 — Full Reset (Nuclear Option 💣)

Delete entire Kubernetes cluster:

```bash
minikube delete
```

---

## 🔄 Recreate Cluster

```bash
minikube start --driver=docker --memory=8144 --cpus=4
```

---

## ⚠️ WARNING

This will delete:

* All Pods
* All Deployments
* All Services
* All ConfigMaps & Secrets
* All Persistent Volumes
* Entire Kubernetes cluster

👉 Use only if everything is broken.

---

# 🔍 Check Existing Namespaces

Before deleting:

```bash
kubectl get ns
```

---

# 🎯 Recommended Command

For most use cases:

```bash
kubectl delete namespace airflow monitoring rtf-data-pipline
```

✔ Fast
✔ Safe
✔ Clean

---

# 💡 Pro Tips

* Use **Safe Cleanup** during development
* Use **Helm Cleanup** before reinstalling apps
* Use **Full Reset** only as last option

---

# 📊 Quick Summary

| Goal             | Command                        |
| ---------------- | ------------------------------ |
| Clean project    | `kubectl delete namespace ...` |
| Remove Helm apps | `helm uninstall ...`           |
| Full reset       | `minikube delete`              |

---

# 🚀 Final Note

Managing cleanup properly is a key skill in Kubernetes.

👉 Keep your environment clean
👉 Avoid resource conflicts
👉 Work like a real production engineer

---
