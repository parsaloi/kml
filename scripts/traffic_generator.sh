#!/bin/bash

TARGET_URL="http://demo-api-service.default.svc.cluster.local:80/"

echo "🚀 Starting KML In-Cluster Traffic Simulation (Offline Mode)..."
echo "---------------------------------------------------"

# Wave 1: Baseline Load (100 QPS)
echo "🌊 Wave 1/3: Baseline Load (100 QPS for 1 minute)"
kubectl run fortio-wave1-$RANDOM --rm -i --image=docker.io/fortio/fortio:latest \
  --image-pull-policy=IfNotPresent --restart=Never --pod-running-timeout=5m -- \
  load -t 1m -qps 100 -c 10 "$TARGET_URL"
sleep 5

# Wave 2: The Uptick (300 QPS)
echo "🌊 Wave 2/3: The Uptick (300 QPS for 1 minute)"
echo "   👉 WATCH YOUR KEDA PODS NOW - THEY SHOULD START PRE-SCALING!"
kubectl run fortio-wave2-$RANDOM --rm -i --image=docker.io/fortio/fortio:latest \
  --image-pull-policy=IfNotPresent --restart=Never --pod-running-timeout=5m -- \
  load -t 1m -qps 300 -c 20 "$TARGET_URL"

echo "⏳ Waiting 30 seconds for pre-scaled pods to reach 'Running' state..."
sleep 30

# Wave 3: The Surge (1,000 QPS)
echo "🌊 Wave 3/3: The Surge (1,000 QPS for 2 minutes)"
kubectl run fortio-wave3-$RANDOM --rm -i --image=docker.io/fortio/fortio:latest \
  --image-pull-policy=IfNotPresent --restart=Never --pod-running-timeout=5m -- \
  load -t 2m -qps 1000 -c 50 "$TARGET_URL"

echo "🏁 Simulation Finished!"
