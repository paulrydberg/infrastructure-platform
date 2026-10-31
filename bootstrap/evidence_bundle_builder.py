#!/usr/bin/env python3
"""PI-5: Incident-evidence bundle builder (deterministic, ADR-0012).

Collects timestamped, checksummed, machine-readable evidence into a single
bundle with a manifest. Builds on PI-1 (platform_state_collector.py).
Contract (ADR-0012): evidence is never fabricated; failed/missing probes are
recorded as explicit error states; missing evidence never becomes a PASS.

Usage:
  python3 evidence_bundle_builder.py -o BUNDLE_DIR [--label LABEL]

Exit codes: 0 bundle complete (may contain failed probes, recorded);
2 fatal (cannot create bundle).
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BUNDLER_VERSION = "1.1.0"
SCHEMA_VERSION = "1.0.0"

# Reuse PI-1 collector as the platform-state evidence source (same directory)
COLLECTOR = Path(__file__).resolve().parent / "platform_state_collector.py"
# PI-4 drift detector: optional probe — if a baseline+observed pair exists in
# the bundle inputs dir (or is passed), its verdict is embedded as evidence.
DRIFT_DETECTOR = Path(__file__).resolve().parent / "drift_detector.py"


def _run(cmd, timeout=120):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        return 1, "", str(e)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _probe(name, cmd, timeout=120):
    """Run one read-only evidence probe. Returns an evidence record —
    failure is DATA (explicit error state), never silence."""
    rc, out, err = _run(cmd, timeout=timeout)
    return {
        "probe": name,
        "command": cmd,
        "exit_code": rc,
        "status": "ok" if rc == 0 else "probe_failed",
        "stdout": out[:20000] if out else "",
        "stderr": (err or "")[:2000],
        "collected_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def collect_evidence(label):
    """Assemble the evidence set: PI-1 snapshot + operational probes."""
    evidence = []
    errors = []

    # PI-1 platform-state snapshot (schema-validated by the collector itself)
    if COLLECTOR.is_file():
        rc, out, err = _run([sys.executable, str(COLLECTOR)], timeout=180)
        if rc == 0:
            try:
                snap = json.loads(out)
                evidence.append({
                    "probe": "pi1_platform_state",
                    "command": [str(COLLECTOR)],
                    "exit_code": 0,
                    "status": "ok",
                    "stdout": out,
                    "stderr": "",
                    "collected_at_utc": snap.get("collected_at_utc", ""),
                    "schema_validated": True,
                })
            except json.JSONDecodeError as e:
                errors.append(f"pi1 snapshot JSON decode failed: {e}")
                evidence.append({
                    "probe": "pi1_platform_state", "command": [str(COLLECTOR)],
                    "exit_code": rc, "status": "malformed_output",
                    "stdout": out[:2000], "stderr": err[:2000],
                    "collected_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                })
        else:
            errors.append(f"pi1 collector exited {rc}: {err[:500]}")
            evidence.append({
                "probe": "pi1_platform_state", "command": [str(COLLECTOR)],
                "exit_code": rc, "status": "probe_failed",
                "stdout": out[:2000], "stderr": err[:2000],
                "collected_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
    else:
        errors.append(f"pi1 collector not found at {COLLECTOR}")

    # Read-only operational probes (fixed set; each failure recorded, not fatal)
    probes = [
        ("docker_ps", ["docker", "ps", "--format",
                       "{{.Names}}\t{{.Status}}\t{{.Image}}"]),
        ("docker_system_df", ["docker", "system", "df"]),
        ("disk_free", ["df", "-g", "/", "/System/Volumes/Data"]),
        ("swap_usage", ["sysctl", "vm.swapusage"]),
        ("host_uptime", ["uptime"]),
    ]
    for name, cmd in probes:
        evidence.append(_probe(name, cmd))

    # PI-4 drift verdict probe (optional inputs — absence is recorded, not fatal)
    baseline = Path(os.environ.get("PI4_BASELINE", ""))
    observed = Path(os.environ.get("PI4_OBSERVED", ""))
    if baseline.is_file() and observed.is_file() and DRIFT_DETECTOR.is_file():
        rc, out, err = _run([sys.executable, str(DRIFT_DETECTOR),
                             "--baseline", str(baseline),
                             "--observed", str(observed)], timeout=120)
        try:
            verdict = json.loads(out)
            evidence.append({
                "probe": "pi4_drift_verdict",
                "command": [str(DRIFT_DETECTOR), "--baseline", str(baseline),
                            "--observed", str(observed)],
                "exit_code": rc,
                "status": "ok" if rc == 0 and verdict.get("verdict") else "malformed_output",
                "stdout": json.dumps(verdict)[:20000],
                "stderr": (err or "")[:2000],
                "collected_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "verdict": verdict.get("verdict"),
                "baseline_id": verdict.get("baseline_id"),
            })
        except json.JSONDecodeError as e:
            evidence.append({
                "probe": "pi4_drift_verdict",
                "command": [str(DRIFT_DETECTOR), "--baseline", str(baseline),
                            "--observed", str(observed)],
                "exit_code": rc, "status": "malformed_output",
                "stdout": out[:2000], "stderr": (err or str(e))[:2000],
                "collected_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
    else:
        evidence.append({
            "probe": "pi4_drift_verdict",
            "command": [],
            "exit_code": 0,
            "status": "skipped_no_inputs",
            "stdout": "",
            "stderr": "",
            "collected_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "note": "PI4_BASELINE/PI4_OBSERVED not both set — drift verdict "
                    "not collected (explicit skip, not silence)",
        })

    return evidence, errors


def build_bundle(bundle_dir, label="unlabeled"):
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    bundle_dir = Path(bundle_dir)
    try:
        bundle_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        return None, [f"bundle dir already exists: {bundle_dir}"]

    evidence, errors = collect_evidence(label)

    files_section = []
    for i, ev in enumerate(evidence):
        fname = f"{i:02d}-{ev['probe']}.json"
        fpath = bundle_dir / fname
        fpath.write_text(json.dumps(ev, indent=2) + "\n")
        files_section.append({
            "file": fname,
            "probe": ev["probe"],
            "status": ev["status"],
            "sha256": sha256_file(fpath),
            "bytes": fpath.stat().st_size,
        })

    failed = [f["probe"] for f in files_section if f["status"] != "ok"]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "bundler_version": BUNDLER_VERSION,
        "label": label,
        "bundle_started_utc": started,
        "bundle_finalized_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "provenance": {
            "tool": "evidence_bundle_builder.py",
            "host": "macmini",
            "llm_inference_required": 0,
            "build_errors": errors,
        },
        "files": files_section,
        "collection_status": ("complete" if not failed and not errors
                              else "complete_with_failed_probes" if not errors
                              else "degraded"),
        "failed_probes": failed,
        "manifest_sha256": None,  # filled below
    }
    mpath = bundle_dir / "manifest.json"
    mpath.write_text(json.dumps(manifest, indent=2) + "\n")
    manifest["manifest_sha256"] = sha256_file(mpath)
    # rewrite with self-hash (hash of manifest without self-reference is stable
    # enough for tamper-evidence; the null-field rewrite is documented behavior)
    mpath.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest, list(errors)


def main(argv):
    out_dir = None
    label = "unlabeled"
    if "-o" in argv:
        i = argv.index("-o")
        if i + 1 < len(argv):
            out_dir = argv[i + 1]
    if "--label" in argv:
        i = argv.index("--label")
        if i + 1 < len(argv):
            label = argv[i + 1]
    if not out_dir:
        print("usage: evidence_bundle_builder.py -o BUNDLE_DIR [--label LABEL]",
              file=sys.stderr)
        return 2
    manifest, errs = build_bundle(out_dir, label)
    if manifest is None:
        print(json.dumps({"error": errs}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps({
        "bundle_dir": out_dir,
        "collection_status": manifest["collection_status"],
        "files": len(manifest["files"]),
        "failed_probes": manifest["failed_probes"],
        "manifest_sha256": manifest["manifest_sha256"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
