#!/usr/bin/env bash
# bootstrap/bootstrap.sh — infrastructure-platform prerequisite validation
#
# Idempotent: safe to run repeatedly; validates rather than installs.
# Philosophy (master spec §10, §69): converge/verify, never mutate.
# Phase 1 scope: VALIDATE prerequisites for the local container foundation.
# Installation of missing prerequisites is deliberately NOT automated yet —
# it is reported so the operator authorizes each host change (spec §32).
#
# Exit codes: 0 = all prerequisites satisfied; 1 = validation failures found.

set -u

PASS=0
FAIL=0
declare -a FAILURES=()
declare -a WARNINGS=()

check() {  # check <name> <command...>
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "PASS  $name"
    PASS=$((PASS+1))
  else
    echo "FAIL  $name"
    FAIL=$((FAIL+1))
    FAILURES+=("$name")
  fi
}

warn_if() {  # warn_if <name> <condition-exit-0-means-warn...>
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "WARN  $name"
    WARNINGS+=("$name")
  fi
}

echo "== infrastructure-platform bootstrap validation =="
echo "-- host --"
check "macOS present"          test "$(uname -s)" = "Darwin"
check "x86_64 architecture"    test "$(uname -m)" = "x86_64"

echo "-- core tools --"
check "git present"            command -v git
check "docker present"         command -v docker
check "docker compose present" docker compose version
check "jq present"             command -v jq
check "gh CLI present"         command -v gh
check "helm present"           bash -c 'command -v helm || test -x "$HOME/tools/bin/helm"'

echo "-- docker engine reachable (shared host: read-only check) --"
if docker info >/dev/null 2>&1; then
  echo "PASS  docker engine reachable"
  PASS=$((PASS+1))
  # Coexistence guard: report (never touch) existing workload count
  RUNNING=$(docker ps --quiet 2>/dev/null | wc -l | tr -d ' ')
  echo "INFO  coexisting running containers: ${RUNNING} (protected; not modified by this project)"
else
  echo "FAIL  docker engine reachable"
  FAIL=$((FAIL+1))
  FAILURES+=("docker engine reachable")
fi

echo "-- resource floors (coexistence-aware; see docs/02-architecture/resource-model.md) --"
FREE_DISK_GB=$(df -g / | awk 'NR==2{print $4}')
if [ "${FREE_DISK_GB:-0}" -ge 50 ]; then
  echo "PASS  free disk >= 50 GiB (${FREE_DISK_GB} GiB)"
  PASS=$((PASS+1))
else
  echo "FAIL  free disk >= 50 GiB (${FREE_DISK_GB:-0} GiB)"
  FAIL=$((FAIL+1))
  FAILURES+=("free disk floor")
fi

echo "-- public-record hygiene: no obvious secrets in working tree --"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1 && \
   git grep -lIinE 'gho_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN[A-Z ]*PRIVATE|AKIA[A-Z0-9]{16}' -- . >/dev/null 2>&1; then
  echo "FAIL  potential secret patterns found in tracked files"
  FAIL=$((FAIL+1))
  FAILURES+=("secret scan")
else
  echo "PASS  secret scan (tracked files)"
  PASS=$((PASS+1))
fi

echo ""
echo "== summary: ${PASS} passed, ${FAIL} failed, ${#WARNINGS[@]} warnings =="
if [ "$FAIL" -gt 0 ]; then
  printf 'missing/failed: %s\n' "${FAILURES[*]}"
  echo "NOTE: this script validates; it does not install. Resolve failures"
  echo "with explicit operator authorization (spec §32 manual-intervention policy)."
  exit 1
fi
exit 0
