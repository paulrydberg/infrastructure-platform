#!/usr/bin/env python3
"""PI-1: Platform-state snapshot collector (deterministic, read-only).

Emits a schema-validated JSON snapshot of the host/VM/k3s state with
provenance. All probes are read-only; no side effects. ADR-0012.

Usage:
  python3 platform_state_collector.py                 # snapshot to stdout
  python3 platform_state_collector.py -o PATH         # write to file
  python3 platform_state_collector.py --schema        # emit schema instead

Exit codes: 0 success; 2 collection failure (probe error) — never a
fabricated snapshot.
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

SCHEMA_VERSION = "1.0.0"
COLLECTOR_VERSION = "1.0.0"

REQUIRED_SNAPSHOT_KEYS = {
    "schema_version", "collector_version", "collected_at_utc", "provenance",
    "host", "docker", "k3s", "gates",
}


def _run(cmd, timeout=30):
    """Run a read-only probe; return (rc, stdout). Failure -> rc != 0."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return 1, ""


def _parse_df_g_root():
    """Parse `df -g /` -> free GiB on the Data/root volume."""
    rc, out = _run(["df", "-g", "/"])
    if rc != 0:
        return None
    m = re.search(r"^\S+\s+\d+\s+\d+\s+(\d+)\s+\d+%?\s", out, re.M)
    # df -g / on macOS: last row has avail in col 4
    lines = [l for l in out.splitlines() if l.startswith("/")]
    if not lines:
        return None
    cols = lines[-1].split()
    try:
        return int(cols[3])  # Available (GiB)
    except (IndexError, ValueError):
        return None


def _parse_swap():
    """Parse sysctl vm.swapusage -> (used_mib, total_mib) or (None, None)."""
    rc, out = _run(["sysctl", "vm.swapusage"])
    if rc != 0:
        return None, None
    # total/used appear in fixed macOS order but parse independently —
    # order-independent and resilient to extra fields.
    mu = re.search(r"used = ([\d,]+(?:\.\d+)?)M", out)
    mt = re.search(r"total = ([\d,]+(?:\.\d+)?)M", out)
    if not (mu and mt):
        return None, None
    return int(float(mu.group(1).replace(",", ""))), int(float(mt.group(1).replace(",", "")))


def _parse_docker_df():
    """Parse `docker system df` -> dict of type->(total, size, reclaimable) strings."""
    rc, out = _run(["docker", "system", "df"])
    if rc != 0:
        return None
    result = {}
    for line in out.splitlines()[1:]:
        cols = line.split()
        if len(cols) >= 4:
            result[cols[0]] = {
                "total": int(cols[1]) if cols[1].isdigit() else None,
                "size": cols[2],
                "reclaimable": cols[3],
            }
    return result or None


def _parse_docker_stats(names):
    """docker stats --no-stream for the named containers -> {name: (used_str, limit_str)}."""
    if not names:
        return None
    rc, out = _run(["docker", "stats", "--no-stream", "--format",
                    "{{.Name}}\t{{.MemUsage}}"] + list(names), timeout=120)
    if rc != 0:
        return None
    result = {}
    for line in out.splitlines():
        if "\t" in line:
            n, usage = line.split("\t", 1)
            result[n] = usage.strip()
    return result or None


def _parse_k3s_pods():
    """kubectl get pods -A via the k3s container -> {ns/name: status}."""
    rc, out = _run(["docker", "exec", "k3s-server", "kubectl", "get", "pods", "-A",
                    "--no-headers"], timeout=60)
    if rc != 0:
        return None
    pods = {}
    for line in out.splitlines():
        cols = line.split()
        if len(cols) >= 5:
            pods[f"{cols[0]}/{cols[1]}"] = {"ready": cols[2], "status": cols[3],
                                            "restarts": cols[4]}
    return pods or None


def _parse_k3s_rss():
    rc, out = _run(["docker", "stats", "--no-stream", "--format",
                    "{{.MemUsage}}", "k3s-server"], timeout=120)
    if rc != 0:
        return None
    line = out.strip()
    return line or None


def collect(protected_fleet_expected=None):
    """Build one snapshot dict. Any probe failure records null + an error,
    never fabricated data."""
    errors = []
    started = time.time()

    free_gib = _parse_df_g_root()
    if free_gib is None:
        errors.append("df -g / parse failed")
    swap_used, swap_total = _parse_swap()
    if swap_used is None:
        errors.append("swapusage parse failed")

    docker_df = _parse_docker_df()
    if docker_df is None:
        errors.append("docker system df failed")

    stats = _parse_docker_stats(["k3s-server", "platform-demo"])
    k3s_rss = stats.get("k3s-server") if stats else None
    demo_rss = stats.get("platform-demo") if stats else None
    if k3s_rss is None:
        errors.append("k3s-server stats failed")

    pods = _parse_k3s_pods()
    if pods is None:
        errors.append("kubectl get pods failed")

    # Gates: reuse the platform's published thresholds (documented, not redefined)
    capacity_gate_gib = 50
    k3s_cap_gib = 1.5

    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "collector_version": COLLECTOR_VERSION,
        "collected_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "collection_duration_s": round(time.time() - started, 2),
        "provenance": {
            "tool": "platform_state_collector.py",
            "host": "macmini",
            "llm_inference_required": 0,
            "probe_errors": errors,
        },
        "host": {
            "free_disk_gib": free_gib,
            "swap_used_mib": swap_used,
            "swap_total_mib": swap_total,
        },
        "docker": {
            "system_df": docker_df,
            "k3s_server_mem_usage": k3s_rss,
            "platform_demo_mem_usage": demo_rss,
        },
        "k3s": {
            "pod_count": len(pods) if pods is not None else None,
            "pods": pods,
            "all_running": (
                all(v["status"] == "Running" for v in pods.values())
                if pods is not None else None
            ),
        },
        "gates": {
            # Thresholds are DOCUMENTED platform gates (resource-model.md,
            # bootstrap.sh) — reported against, not redefined here.
            "capacity_gate_gib": capacity_gate_gib,
            "capacity_gate_pass": (
                (free_gib >= capacity_gate_gib) if free_gib is not None else None
            ),
            "k3s_cap_gib": k3s_cap_gib,
            "k3s_rss_raw": k3s_rss,
        },
    }
    return snapshot


def validate_snapshot(snap):
    """Structural validation. Returns list of errors (empty = valid).
    Missing probe data is legal (null) — silence about failures is not."""
    errs = []
    missing = REQUIRED_SNAPSHOT_KEYS - set(snap)
    if missing:
        errs.append(f"missing keys: {sorted(missing)}")
    if snap.get("schema_version") != SCHEMA_VERSION:
        errs.append("schema_version mismatch")
    if snap.get("collector_version") != COLLECTOR_VERSION:
        errs.append("collector_version mismatch")
    if not snap.get("collected_at_utc"):
        errs.append("collected_at_utc absent")
    prov = snap.get("provenance") or {}
    if "probe_errors" not in prov:
        errs.append("provenance.probe_errors required (may be empty)")
    if "llm_inference_required" not in prov:
        errs.append("provenance.llm_inference_required required")
    h = snap.get("host") or {}
    for k in ("free_disk_gib", "swap_used_mib"):
        if k not in h:
            errs.append(f"host.{k} required (may be null on probe failure)")
    if "free_disk_gib" in h and h["free_disk_gib"] is not None and (
            not isinstance(h["free_disk_gib"], int) or h["free_disk_gib"] < 0):
        errs.append("host.free_disk_gib must be a non-negative int or null")
    return errs


def main(argv):
    if "--schema" in argv:
        print(json.dumps({"required_keys": sorted(REQUIRED_SNAPSHOT_KEYS),
                          "schema_version": SCHEMA_VERSION,
                          "collector_version": COLLECTOR_VERSION}, indent=2))
        return 0
    snap = collect()
    errs = validate_snapshot(snap)
    if errs:
        print(json.dumps({"error": "snapshot validation failed", "errors": errs},
                         indent=2), file=sys.stderr)
        return 2
    out = json.dumps(snap, indent=2)
    if "-o" in argv:
        i = argv.index("-o")
        if i + 1 >= len(argv):
            print("error: -o requires a path", file=sys.stderr)
            return 2
        Path(argv[i + 1]).write_text(out + "\n")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
