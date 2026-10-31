#!/usr/bin/env python3
"""PI-3: Deployment-readiness evaluator (deterministic, ADR-0012).

Consumes a PI-1 platform-state snapshot and the platform's DOCUMENTED gate
thresholds, and emits a machine-readable READY/NOT_READY verdict with
per-criterion evidence. Reuses existing published gates verbatim — it does
not define new ones, and it can never upgrade an UNKNOWN to a PASS.

Usage:
  python3 deployment_readiness_evaluator.py snapshot.json
  python3 deployment_readiness_evaluator.py snapshot.json -o verdict.json

Exit codes: 0 evaluated; 2 input/validation error.
"""
import json
import sys
import time
from pathlib import Path

EVALUATOR_VERSION = "1.0.0"

# ── Documented platform gates (resource-model.md / bootstrap.sh / reconstruct.sh)
# Verbatim values; DO NOT edit here to make a verdict pass. This block mirrors
# published platform policy and is drift-guarded by the test suite.
THRESHOLDS = {
    # bootstrap.sh: free disk >= 50 GiB prerequisite (deployment gate)
    "capacity_gate_gib": 50,
    # reconstruct.sh memory gate: free% >= 35 at pressure NORMAL
    "mem_free_pct_min": 35,
    # docker VM total memory (GiB) — measured envelope
    "docker_vm_total_gib": 7.654,
    # k3s container cap GiB (Phase-2 A'' envelope)
    "k3s_cap_gib": 1.5,
}

VERDICT_READY = "READY"
VERDICT_NOT_READY = "NOT_READY"
VERDICT_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


def _k3s_rss_gib(rss_raw):
    """'1.11GiB / 1.5GiB' -> 1.11 (float) or None."""
    if not rss_raw or "GiB" not in rss_raw:
        return None
    try:
        return float(rss_raw.split("GiB")[0].strip())
    except ValueError:
        return None


def evaluate(snapshot):
    """Evaluate one PI-1 snapshot. Returns verdict dict.
    Any missing measurement -> that criterion UNKNOWN; snapshot-level
    missing data -> INSUFFICIENT_DATA (never NOT_READY inferred as PASS)."""
    errs = []

    required = {"collected_at_utc", "host", "docker", "k3s", "gates"}
    missing = required - set(snapshot)
    if missing:
        return {"verdict": VERDICT_INSUFFICIENT_DATA,
                "evaluator_version": EVALUATOR_VERSION,
                "evaluated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "snapshot_collected_at_utc": None,
                "criteria": [],
                "errors": [f"snapshot missing keys: {sorted(missing)}"]}

    host = snapshot.get("host") or {}
    k3s = snapshot.get("k3s") or {}
    docker = snapshot.get("docker") or {}
    criteria = []

    # C1: capacity gate (deployment gate, documented 50 GiB)
    free = host.get("free_disk_gib")
    if free is None:
        c1 = "UNKNOWN"
    elif free >= THRESHOLDS["capacity_gate_gib"]:
        c1 = "PASS"
    else:
        c1 = "FAIL"
    criteria.append({
        "criterion": "capacity_gate",
        "verdict": c1,
        "threshold": {"free_disk_gib_min": THRESHOLDS["capacity_gate_gib"]},
        "measured": {"free_disk_gib": free},
        "source": "bootstrap.sh prerequisite (deployment gate; deployment-specific)",
    })

    # C2: k3s pod health (control plane readiness)
    pods = k3s.get("pods")
    if pods is None:
        c2 = "UNKNOWN"
        meas = None
    else:
        bad = {name: p for name, p in pods.items()
               if p.get("status") != "Running" or not str(p.get("ready", "")).startswith(("1/1", "0/")) and not p.get("ready", "").endswith("Running")}
        # simpler: status must be Running and ready must not contain '0/'
        bad = {name: p for name, p in pods.items()
               if p.get("status") != "Running" or "0/" in str(p.get("ready", ""))}
        meas = {"pod_count": len(pods), "not_ready": bad}
        c2 = "PASS" if not bad else "FAIL"
    criteria.append({
        "criterion": "k3s_pods_healthy",
        "verdict": c2,
        "threshold": {"all_pods_running_and_ready": True},
        "measured": meas,
        "source": "kubectl get pods -A via k3s-server (PI-1 snapshot)",
    })

    # C3: k3s memory envelope (cap 1.5 GiB; warn above 90% of cap)
    rss_raw = (docker.get("k3s_server_mem_usage"))
    rss = _k3s_rss_gib(rss_raw)
    if rss is None:
        c3 = "UNKNOWN"
        meas3 = None
    else:
        warn_line = THRESHOLDS["k3s_cap_gib"] * 0.9
        c3 = "PASS" if rss < warn_line else ("WARN" if rss <= THRESHOLDS["k3s_cap_gib"] else "FAIL")
        meas3 = {"k3s_rss_gib": rss, "cap_gib": THRESHOLDS["k3s_cap_gib"],
                 "warn_line_gib": round(warn_line, 3)}
    criteria.append({
        "criterion": "k3s_memory_envelope",
        "verdict": c3,
        "threshold": {"warn_at_pct_of_cap": 90},
        "measured": meas3,
        "source": "docker stats k3s-server (PI-1 snapshot); Phase-2 A'' envelope",
    })

    # C4: swap activity sanity — swap residency alone is NOT a failure
    # (resource-gate-principles.md: residency != pressure). Without a
    # pressure probe in the snapshot this criterion stays informational.
    swap_used = host.get("swap_used_mib")
    criteria.append({
        "criterion": "swap_residency_informational",
        "verdict": "INFO" if swap_used is not None else "UNKNOWN",
        "threshold": None,
        "measured": {"swap_used_mib": swap_used},
        "source": "resource-gate-principles.md: residency != pressure; not a gate",
    })

    blocking = [c for c in criteria if c["verdict"] in ("FAIL",)]
    unknowns = [c for c in criteria if c["verdict"] == "UNKNOWN"]

    if unknowns and not blocking:
        verdict = VERDICT_INSUFFICIENT_DATA
    elif blocking:
        verdict = VERDICT_NOT_READY
    else:
        verdict = VERDICT_READY

    return {
        "verdict": verdict,
        "evaluator_version": EVALUATOR_VERSION,
        "evaluated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "snapshot_collected_at_utc": snapshot.get("collected_at_utc"),
        "thresholds": THRESHOLDS,
        "criteria": criteria,
        "blocking": [c["criterion"] for c in blocking],
        "unknown": [c["criterion"] for c in unknowns],
        "llm_inference_required": 0,
        "errors": errs,
    }


def main(argv):
    if not argv:
        print("usage: deployment_readiness_evaluator.py snapshot.json [-o out.json]",
              file=sys.stderr)
        return 2
    src = Path(argv[0])
    if not src.is_file():
        print(f"error: snapshot not found: {src}", file=sys.stderr)
        return 2
    try:
        snapshot = json.loads(src.read_text())
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON: {e}", file=sys.stderr)
        return 2
    verdict = evaluate(snapshot)
    out = json.dumps(verdict, indent=2)
    if "-o" in argv:
        i = argv.index("-o")
        if i + 1 < len(argv):
            Path(argv[i + 1]).write_text(out + "\n")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
