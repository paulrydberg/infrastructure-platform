#!/bin/bash
# =============================================================================
# bootstrap/level6-readiness-check.sh — thin deterministic wrapper for the
# Level 6 readiness observer (cron entry point).
#
# Architecture boundary (documented in docs/15-reproducibility/):
#   launchd -> Level 6 RECONSTRUCTION (bootstrap/periodic-validate.sh)
#   cron    -> Level 6 OBSERVER (this script): reads evidence, evaluates
#              deterministic readiness, reminds operator. No inference, no
#              Docker/K8s/Argo, no Git mutation, no reconstruction runs.
#
# Cron is invoked non-interactively with a minimal environment; this wrapper
# pins PATH explicitly (no ambient dependency) and uses absolute paths.
# =============================================================================
set -u
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin"
REPO="/Users/macmini/.hermes/projects/infrastructure-platform"
exec /usr/bin/python3 "$REPO/bootstrap/level6-readiness-check.py" --notify "$@"
