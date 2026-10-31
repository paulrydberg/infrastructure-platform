#!/usr/bin/env python3
"""PI-2/PI-6 evidence-window validator (deterministic, ADR-0012).

Measures whether a directory of PI-1 snapshot JSON files meets the
documented evidence-quality criteria (pi1-scheduling-proposal.md):

  C1 coverage      ≥ COVERAGE_MIN of expected hourly samples in the window
  C2 schema-valid  ≥ SCHEMA_VALID_MIN of snapshots parse + carry provenance
  C3 gap discipline  no gap between consecutive snapshots > MAX_GAP_S
  C4 threshold stability  gates.capacity_gate_gib constant across the window

Output: machine-readable verdict, zero inference. A window that does not
qualify yields QUALIFIED=false with per-criterion evidence — PI-2/PI-6 must
treat any non-qualifying window as INSUFFICIENT_DATA, never as a trend basis.

Usage:
  python3 evidence_window_validator.py --dir ~/.infrastructure-platform/pi1-snapshots \
      [--days 14] [-o verdict.json]

Exit codes: 0 evaluated; 2 input error.
"""
import argparse
import calendar
import json
import sys
import time
from pathlib import Path

VALIDATOR_VERSION = "1.0.0"

# Criteria (documented in pi1-scheduling-proposal.md; mirrors ADR-0012 review)
COVERAGE_MIN = 0.90          # C1: ≥90% of expected hourly slots present
SCHEMA_VALID_MIN = 0.95      # C2: ≥95% snapshots structurally valid
MAX_GAP_S = 6 * 3600         # C3: no gap > 6 h between consecutive snapshots
# C4: capacity_gate_gib must be a single distinct value across the window


def _parse_utc(ts):
    try:
        return calendar.timegm(time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ"))
    except (TypeError, ValueError):
        return None


def _load_snapshots(dirpath, days):
    """Load snapshots within the trailing N-day window.
    Returns (records, malformed) — both are evidence."""
    d = Path(dirpath)
    if not d.is_dir():
        return None, [f"snapshot dir not found: {d}"]
    now = calendar.timegm(time.gmtime())
    cutoff = now - days * 86400
    records, malformed = [], []
    for p in sorted(d.glob("pi1-*.json")):
        try:
            rec = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            malformed.append({"file": p.name, "error": str(e)})
            continue
        ts = _parse_utc(rec.get("collected_at_utc"))
        if ts is None:
            malformed.append({"file": p.name, "error": "unparseable collected_at_utc"})
            continue
        if ts >= cutoff:
            records.append({"file": p.name, "ts": ts, "record": rec})
    return records, malformed


def validate_window(dirpath, days=14, now_s=None):
    """Evaluate the quality criteria. Deterministic; no inference."""
    errors = []
    records, malformed = _load_snapshots(dirpath, days)
    if records is None:
        # _load_snapshots returns ([], [error]) for unreadable dir — surface it
        dir_errors = [e if isinstance(e, str) else
                      f"malformed: {e.get('file')}: {e.get('error')}"
                      for e in (malformed or [])]
        return {
            "window_qualified": False,
            "validator_version": VALIDATOR_VERSION,
            "criteria": {"coverage_min": COVERAGE_MIN,
                         "schema_valid_min": SCHEMA_VALID_MIN,
                         "max_gap_s": MAX_GAP_S},
            "snapshot_dir": str(dirpath),
            "window_days": days,
            "errors": dir_errors or [f"snapshot dir not found or unreadable: {dirpath}"],
            "llm_inference_required": 0,
        }, False

    now = now_s if now_s is not None else calendar.timegm(time.gmtime())
    n = len(records)

    # C1 — coverage: unique hourly slots vs expected slots in window
    hours = sorted({r["ts"] // 3600 for r in records})
    expected_hours = days * 24
    coverage = (len(hours) / expected_hours) if expected_hours else 0.0
    c1_pass = coverage >= COVERAGE_MIN

    # C2 — schema validity: required keys + provenance + gate value readable
    valid = 0
    for r in records:
        rec = r["record"]
        gates = rec.get("gates") or {}
        ok = (isinstance(rec.get("host"), dict)
              and rec.get("host", {}).get("free_disk_gib") is not None
              and rec.get("collected_at_utc")
              and "capacity_gate_gib" in gates)
        if ok:
            valid += 1
    schema_ratio = (valid / n) if n else 0.0
    c2_pass = schema_ratio >= SCHEMA_VALID_MIN
    if valid < n:
        errors.append(f"{n - valid} parseable snapshot(s) missing required "
                      f"evidence keys (host.free_disk_gib / gates) — counted "
                      f"against schema validity")

    # C3 — gap discipline
    gaps = []
    max_gap = 0
    for a, b in zip(hours, hours[1:]):
        gap = (b - a) * 3600
        gaps.append(gap)
        max_gap = max(max_gap, gap)
    c3_pass = max_gap <= MAX_GAP_S

    # C4 — threshold stability
    thresholds = {r["record"]["gates"]["capacity_gate_gib"] for r in records
                  if "capacity_gate_gib" in (r["record"].get("gates") or {})}
    c4_pass = len(thresholds) == 1

    criteria_results = {
        "c1_coverage": {"pass": c1_pass, "coverage": round(coverage, 4),
                        "unique_hours": len(hours), "expected_hours": expected_hours,
                        "min": COVERAGE_MIN},
        "c2_schema_valid": {"pass": c2_pass, "ratio": round(schema_ratio, 4),
                            "valid": valid, "total": n,
                            "min": SCHEMA_VALID_MIN},
        "c3_gap_discipline": {"pass": c3_pass, "max_gap_s": max_gap,
                              "max_allowed_s": MAX_GAP_S},
        "c4_threshold_stability": {"pass": c4_pass,
                                   "distinct_values": sorted(thresholds, key=str)},
    }
    qualified = c1_pass and c2_pass and c3_pass and c4_pass and n > 0
    if malformed:
        errors.append(f"{len(malformed)} malformed snapshot(s) excluded: "
                      + ", ".join(m["file"] for m in malformed[:5]))

    verdict = {
        "window_qualified": qualified,
        "validator_version": VALIDATOR_VERSION,
        "snapshot_dir": str(dirpath),
        "window_days": days,
        "evaluated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "snapshot_count": n,
        "malformed_count": len(malformed),
        "criteria": {"coverage_min": COVERAGE_MIN,
                     "schema_valid_min": SCHEMA_VALID_MIN,
                     "max_gap_s": MAX_GAP_S},
        "criteria_results": criteria_results,
        "errors": errors,
        "llm_inference_required": 0,
        "read_only": True,
        "note": ("window QUALIFIED for PI-2/PI-6 consumption" if qualified else
                 "window NOT qualified — PI-2/PI-6 must treat as "
                 "INSUFFICIENT_DATA; a calendar fortnight alone does not "
                 "unlock them"),
    }
    return verdict, qualified


def malformed_errors(malformed):
    return [f"malformed: {m['file']}: {m['error']}" for m in malformed]


def main(argv=None):
    ap = argparse.ArgumentParser(description="PI-2/PI-6 evidence-window validator")
    ap.add_argument("--dir", required=True)
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("-o", dest="out")
    args = ap.parse_args(argv)

    verdict, _ = validate_window(args.dir, days=args.days)
    out = json.dumps(verdict, indent=2)
    if args.out:
        Path(args.out).write_text(out + "\n")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
