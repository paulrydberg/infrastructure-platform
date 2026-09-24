#!/bin/bash
# Tier-A metrics-server observation sampler — one sample per invocation.
# Appends a single line to artifacts/tier-a-observation.log
cd /Users/macmini/.hermes/projects/infrastructure-platform
export PATH=/usr/local/bin:$PATH
K="docker exec k3s-server kubectl"
k3s=$(docker stats --no-stream --format '{{.MemUsage}}' k3s-server | awk -F/ '{print $1}' | tr -d ' ')
vmavail=$(docker run --rm alpine:3.20 free -m | awk '/Mem:/{print $6}')
swap=$(sysctl vm.swapusage | awk -F'= ' '{print $3}' | awk -F'M' '{print $1}' | tr -d ' ')
load5=$(uptime | awk -F'load averages:' '{print $2}' | awk '{print $2}')
T0=$(python3 -c 'import time;print(time.time())')
$K get --raw=/readyz >/dev/null 2>&1
T1=$(python3 -c 'import time;print(time.time())')
api=$(python3 -c "print(f'{$T1-$T0:.2f}')")
argo=$($K get application platform-demo -n argocd -o jsonpath='{.status.sync.status} {.status.health.status}' 2>/dev/null)
ms=$($K get pods -n kube-system -l k8s-app=metrics-server --no-headers 2>/dev/null | awk '{print $3}')
demo=$($K get pods -n platform-demo --no-headers 2>/dev/null | awk '{print $3}')
prot=$(docker ps --format '{{.Names}}' | grep -v 'platform-demo\|k3s' | while read c; do docker inspect "$c" --format '{{.State.Status}} restarts={{.RestartCount}} oom={{.State.OOMKilled}}'; done | grep -vE 'running restarts=(0|1) oom=false' | wc -l | tr -d ' ')
echo "$(date +%H:%M) sample: k3s=$k3s | VMavail=${vmavail}MB | swap=${swap}MB | load5=$load5 | API=${api}s | argo=$argo | ms=$ms demo=$demo | protected_anomalies=$prot" >> artifacts/tier-a-observation.log
