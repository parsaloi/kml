# KML: Proactive Event-Driven Autoscaling (KEDA + ML)

This repository demonstrates the KML (KEDA + Machine Learning) conceptual framework. It illustrates how to move away from reactive autoscaling (HPA/VPA) by leveraging time-series forecasting (Facebook Prophet) to preemptively scale Kubernetes workloads before traffic spikes occur.

## Architecture Overview

1. **Telemetry:** Prometheus collects live traffic metrics.
2. **Intelligence:** A lightweight Python microservice uses Facebook Prophet to ingest historical/live metrics and project demand 5 minutes into the future.
3. **Execution:** KEDA (Kubernetes Event-driven Autoscaling) reads this forecasted metric via Prometheus and scales the application preemptively, eliminating cold-start latency.

## Prerequisites (16GB memory Environment)

This POC is designed to run locally on a dev machine. 16GB of RAM is sufficient for this stack.

* **Docker Desktop**: Ensure the WSL2 backend is enabled (Settings > General > Use the WSL 2 based engine). Allocate at least 4GB RAM to WSL if configured manually via `.wslconfig`.
* **WSL2 / PowerShell**: The commands below can be run in PowerShell or a WSL2 terminal (Ubuntu).
* **CLI Tools**:
  * [Kind](https://kind.sigs.k8s.io/) (Kubernetes IN Docker)
  * [kubectl](https://kubernetes.io/docs/tasks/tools/)
  * [Helm](https://helm.sh/docs/intro/install/)

## 1. Bootstrap the Local Cluster

Create a local Kubernetes cluster and install the required infrastructure (KEDA and Prometheus).

```bash
# Create a local kind cluster
kind create cluster --name kml-cluster

# Add Helm repositories
helm repo add keda [https://kedacore.github.io/charts](https://kedacore.github.io/charts)
helm repo add prometheus-community [https://prometheus-community.github.io/helm-charts](https://prometheus-community.github.io/helm-charts)
helm repo update

# Install KEDA
helm install keda keda/keda --namespace keda --create-namespace

# Install Prometheus (lightweight for POC)
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring --create-namespace \
  --set server.persistentVolume.enabled=false \
  --set alertmanager.enabled=false \
  --set pushgateway.enabled=false
