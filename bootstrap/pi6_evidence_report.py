#!/usr/bin/env python3
"""PI-6 evidence report generator — deterministic, zero-inference.

Produces a schema-valid report from ALREADY-COMPUTED evidence:
  - one PI-1 platform-state snapshot (latest, or an explicit file)
  - the evidence-window verdict for its directory (computed here)
  - the PI-3 deployment-readiness verdict for that snapshot (computed here)

AUTHORITY MODEL (ADR-0012; mirrors report-authority invariant L4-6):
  AUTHORITATIVE   only when the evidence window is QUALIFIED, the snapshot
                  is fresh (< STALENESS_S), and every verdict resolved.
  ADVISORY_ONLY   evidence present but window unqualified — readable, but
                  explicitly marked as NOT qualifying any downstream gate.
  INSUFFICIENT_DATA inputs missing/invalid — fail-closed; nothing invented.

The report never flips a gate. PI-2/PI-6 unlock criteria are checked, never
weakened: an unqualified window is reported as such, honestly.

Usage:
  python3 pi6_evidence_report.py <snapshot-dir> [-o report.json]
  python3 pi6_evidence_report.py <snapshot-dir> --snapshot <file.json>

Exit codes: 0 report written · 1 fail-closed (nothing fabricated).
"""

import argparse
import calendar
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

REPORT_VERSION = "1.0.0"
STALENESS_S = 6 * 3600          # mirrors PI-2/PI-6 staleness bound
HERE = Path(__file__).resolve().parent


def _import(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_report(snapshot_dir, snapshot_file=None, now_s=None):
    """Assemble the report. Deterministic given identical evidence.
    Returns (report, errors) — errors non-empty means fail-closed."""
    errors = []
    now = now_s if now_s is not None else calendar.timegm(time.gmtime())

    evw = _import("evw", HERE / "evidence_window_validator.py")
    ev3 = _import("ev3", HERE / "deployment_readiness_evaluator.py")

    # ── evidence window verdict ──────────────────────────────────────────
    window, w_ok = evw.validate_window(snapshot_dir, days=14, now_s=now)

    # ── snapshot selection: explicit file, else newest valid ─────────────
    d = Path(snapshot_dir)
    if snapshot_file:
        snap_path = Path(snapshot_file)
    else:
        candidates = sorted(d.glob("pi1-*.json")) if d.is_dir() else []
        snap_path = candidates[-1] if candidates else None
    if snap_path is None or not snap_path.is_file():
        return None, [f"no PI-1 snapshot available in {d} — "
                      f"INSUFFICIENT_DATA (absence is never success)"]

    try:
        snap = json.loads(snap_path.read_text())
    except json.JSONDecodeError as e:
        return None, [f"snapshot {snap_path.name} unparseable: {e}"]

    collected = evw._parse_utc(snap.get("collected_at_utc"))
    if collected is None:
        return None, [f"snapshot {snap_path.name} has unparseable "
                      f"collected_at_utc"]
    age_s = now - collected
    stale = age_s > STALENESS_S

    # ── PI-3 readiness verdict for this snapshot ─────────────────────────
    pi3 = ev3.evaluate(snap)
    pi3_errors = pi3.get("errors") or []
    if pi3_errors:
        errors.extend(f"pi3: {e}" for e in pi3_errors)

    snap_sha = _sha256_file(snap_path)

    # ── authority determination (fail-closed, deterministic) ─────────────
    qualified = bool(window.get("window_qualified"))
    pi3_clean = not pi3_errors and pi3.get("verdict") in ("READY", "NOT_READY")
    if qualified and pi3_clean and not stale and not window.get("errors"):
        authority = "AUTHORITATIVE"
    elif qualified and not stale:
        # window qualified but a verdict component is degraded
        authority = "ADVISORY_ONLY"
        if not pi3_clean:
            errors.append("authority reduced: PI-3 verdict missing/degraded")
    else:
        authority = "ADVISORY_ONLY"
        if not qualified:
            failed = [k for k, v in window.get("criteria_results", {}).items()
                      if isinstance(v, dict) and not v.get("pass")]
            errors.append("authority reduced: evidence window not qualified"
                          + (f" (failed criteria: {', '.join(failed)})"
                             if failed else " (anomalies present)"))
        if stale:
            errors.append(f"authority reduced: snapshot stale "
                          f"({age_s // 3600}h old > {STALENESS_S // 3600}h)")

    report = {
        "schema_version": "1.0.0",
        "report_version": REPORT_VERSION,
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                          time.gmtime(now)),
        "authority": authority,
        "llm_inference_required": 0,
        "evidence": {
            "snapshot_file": snap_path.name,
            "snapshot_sha256": snap_sha,
            "snapshot_collected_at_utc": snap.get("collected_at_utc"),
            "snapshot_age_s": age_s,
            "snapshot_stale": stale,
            "window_qualified": qualified,
            "window_criteria": window.get("criteria_results"),
            "window_errors": window.get("errors"),
        },
        "pi3_readiness": {
            "verdict": pi3.get("verdict"),
            "evaluator_version": pi3.get("evaluator_version"),
        },
        "provenance": {
            "report_version": REPORT_VERSION,
            "validator_version": window.get("validator_version"),
            "inputs_hashed": True,
        },
        "note": ("authoritative: qualified window + fresh snapshot + resolved "
                 "verdicts" if authority == "AUTHORITATIVE" else
                 "ADVISORY_ONLY — does not satisfy PI-2/PI-6 unlock gates; "
                 "an unqualified window is never upgraded by elapsed time"),
    }
    return report, errors


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("snapshot_dir")
    ap.add_argument("--snapshot", default=None,
                    help="explicit snapshot file (default: newest in dir)")
    ap.add_argument("-o", "--output", default=None,
                    help="write report JSON here (stdout if omitted)")
    args = ap.parse_args()

    report, errors = build_report(args.snapshot_dir, args.snapshot)
    if report is None:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1

    out = json.dumps(report, indent=2, sort_keys=False)
    if args.output:
        out_p = Path(args.output)
        if out_p.exists():
            print(f"FAIL: refusing to overwrite {out_p} "
                  f"(no-overwrite rule)", file=sys.stderr)
            return 1
        out_p.write_text(out)
    print(out)
    if errors:
        # visible degradation, still a valid advisory report
        for e in errors:
            print(f"NOTE: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
