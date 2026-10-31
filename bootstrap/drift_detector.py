#!/usr/bin/env python3
"""PI-4: Drift detector (deterministic, repository-only, ADR-0012).

Compares OBSERVED cluster state against the Git-DECLARED baseline and emits
a machine-readable verdict with explicit evidence provenance.

Verdicts (fail-closed):
  CONVERGED           observed matches declared on every comparable field
  DRIFT               at least one declared field differs from observed
  STALE_EVIDENCE      observed record is older than max_age_s (not a pass)
  INSUFFICIENT_DATA   missing/malformed/incomparable inputs (never a pass)
  SCHEMA_MISMATCH     record schema_version differs from the declared baseline

Drift vs runtime variation: spec-level declared fields (image tag, replicas,
resources, security context) are CONFIGURATION. Restart counts, pod status,
and timestamps are RUNTIME VARIATION and are explicitly excluded from
comparison — a crashlooping pod is a readiness concern (PI-3), not drift.

This tool is READ-ONLY: it never modifies the infrastructure it evaluates.
It compares two JSON records (baseline + observed) produced by collectors;
live probe wiring is deliberately NOT included so the comparison logic is
fully testable without touching the cluster (see
pi4-drift-detector-tests.py; live drift-injection validation is a separate,
authorization-gated step).

Usage:
  python3 drift_detector.py --baseline baseline.json --observed observed.json
      [--max-age-s 900] [-o verdict.json]

Exit codes: 0 evaluated (verdict may be DRIFT); 2 input error.
"""
import argparse
import calendar
import hashlib
import json
import sys
import time
from pathlib import Path

DETECTOR_VERSION = "1.1.0"
SCHEMA_VERSION = "1.0.0"

# ── Declared-field contract ────────────────────────────────────────────────
# Fields compared (configuration — drift candidates). Sources:
#   platform/helm/platform-demo/values.yaml  (replicaCount, image.tag,
#     resources, securityContext) rendered through the Helm templates.
#   platform/argocd/application-platform-demo.yaml (targetRevision, sync
#     policy). Runtime-variation fields (restarts, pod status, timestamps)
#     are deliberately NOT listed here.
DECLARED_FIELDS = {
    "deployment.replicas": ("replicas",),
    "deployment.image_tag": ("image_tag",),
    "deployment.memory_limit": ("resources", "limits", "memory"),
    "deployment.cpu_limit": ("resources", "limits", "cpu"),
    "deployment.run_as_non_root": ("security_context", "run_as_non_root"),
    "deployment.read_only_root_fs": ("security_context", "read_only_root_filesystem"),
}

RUNTIME_VARIATION_FIELDS = (
    # recorded for context, never compared
    "restarts", "status", "collected_at_utc", "pod_phase",
)

REQUIRED_RECORD_KEYS = {"schema_version", "record_type", "collected_at_utc", "state"}

VERDICT_CONVERGED = "CONVERGED"
VERDICT_DRIFT = "DRIFT"
VERDICT_STALE = "STALE_EVIDENCE"
VERDICT_INSUFFICIENT = "INSUFFICIENT_DATA"
VERDICT_SCHEMA = "SCHEMA_MISMATCH"


def _load_json(path):
    """Load a record file. Returns (record|None, error|None)."""
    p = Path(path)
    if not p.is_file():
        return None, f"file not found: {p}"
    try:
        return json.loads(p.read_text()), None
    except json.JSONDecodeError as e:
        return None, f"malformed JSON: {e}"


def _record_errors(record, expected_type):
    """Structural validation. Missing probe data is legal (null) — silence
    about failures is not."""
    errs = []
    if not isinstance(record, dict):
        return [f"record is {type(record).__name__}, expected object"]
    missing = REQUIRED_RECORD_KEYS - set(record)
    if missing:
        errs.append(f"missing keys: {sorted(missing)}")
    if record.get("record_type") not in (None, expected_type):
        errs.append(f"record_type mismatch: expected {expected_type}")
    if not record.get("collected_at_utc"):
        errs.append("collected_at_utc absent (provenance required)")
    return errs


def _age_s(record, now_s=None):
    """Seconds since collected_at_utc, or None if unparseable.
    Timestamps are UTC — calendar.timegm, not mktime (local offset)."""
    ts = (record or {}).get("collected_at_utc")
    if not ts:
        return None
    try:
        t = time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    now = now_s if now_s is not None else calendar.timegm(time.gmtime())
    return max(0, now - calendar.timegm(t))


_MISSING = object()  # sentinel: field absent — distinct from an explicit null


def _get_path(d, path):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return _MISSING, True  # absent
        cur = cur[k]
    return cur, False


def compare(baseline, observed, now_s=None, max_age_s=900):
    """Deterministic comparison. Returns verdict dict.

    Any missing/stale/malformed/incomparable input yields a fail-closed
    verdict — never a clean bill of health."""
    errors = []

    berrs = _record_errors(baseline, "declared_state")
    oerrs = _record_errors(observed, "observed_state")
    if berrs:
        errors.append(f"baseline: {'; '.join(berrs)}")
    if oerrs:
        errors.append(f"observed: {'; '.join(oerrs)}")
    if errors:
        return _verdict(VERDICT_INSUFFICIENT, errors, baseline, observed)
    if baseline.get("schema_version") != SCHEMA_VERSION or \
       observed.get("schema_version") != SCHEMA_VERSION:
        return _verdict(VERDICT_SCHEMA,
                        [f"baseline={baseline.get('schema_version')} "
                         f"observed={observed.get('schema_version')} "
                         f"expected={SCHEMA_VERSION}"],
                        baseline, observed)

    age = _age_s(observed, now_s)
    if age is None:
        return _verdict(VERDICT_INSUFFICIENT,
                        ["observed.collected_at_utc unparseable"],
                        baseline, observed)
    if age > max_age_s:
        return _verdict(VERDICT_STALE,
                        [f"observed age {int(age)}s exceeds max_age_s={max_age_s}"],
                        baseline, observed)

    b_state = baseline.get("state") or {}
    o_state = observed.get("state") or {}
    fields = []
    drifts = []
    incomparable = []
    for name, path in sorted(DECLARED_FIELDS.items()):
        bval, bmiss = _get_path(b_state, path)
        oval, omiss = _get_path(o_state, path)
        # An explicit null VALUE is data; an ABSENT field is missing evidence.
        # null vs absent must never report MATCH (it would conceal change).
        rec = {"field": name,
               "declared": None if bmiss else bval,
               "observed": None if omiss else oval}
        if bmiss or omiss:
            rec["comparison"] = "INCOMPARABLE_MISSING"
            incomparable.append(name)
        elif bval == oval:
            rec["comparison"] = "MATCH"
        else:
            rec["comparison"] = "MISMATCH"
            drifts.append(name)
        fields.append(rec)

    verdict = VERDICT_DRIFT if drifts else (
        VERDICT_INSUFFICIENT if incomparable else VERDICT_CONVERGED)
    if incomparable and not drifts:
        errors.append(f"incomparable fields (missing in one record): {incomparable}")
    return _verdict(verdict, errors, baseline, observed, fields=fields,
                    drifts=drifts, incomparable=incomparable)


def baseline_identity(baseline):
    """Deterministic content hash over the declared state (canonical JSON).
    Versioned baseline identity: same declared content ⇒ same id, regardless
    of unrelated metadata (timestamps, labels). None if baseline unusable."""
    if not isinstance(baseline, dict):
        return None
    state = baseline.get("state")
    if not isinstance(state, dict):
        return None
    try:
        canon = json.dumps(state, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canon.encode()).hexdigest()
    except (TypeError, ValueError):
        return None


def _verdict(verdict, errors, baseline, observed, fields=None, drifts=None,
             incomparable=None):
    return {
        "verdict": verdict,
        "detector_version": DETECTOR_VERSION,
        "schema_version": SCHEMA_VERSION,
        "baseline_id": baseline_identity(baseline),
        "evaluated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "baseline_collected_at_utc": (baseline or {}).get("collected_at_utc"),
        "observed_collected_at_utc": (observed or {}).get("collected_at_utc"),
        "compared_fields": fields or [],
        "drifted_fields": drifts or [],
        "incomparable_fields": incomparable or [],
        "runtime_variation_excluded": list(RUNTIME_VARIATION_FIELDS),
        "errors": errors,
        "llm_inference_required": 0,
        "read_only": True,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="PI-4 deterministic drift detector")
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--observed", required=True)
    ap.add_argument("--max-age-s", type=int, default=900)
    ap.add_argument("-o", dest="out")
    args = ap.parse_args(argv)

    baseline, berr = _load_json(args.baseline)
    observed, oerr = _load_json(args.observed)
    if berr or oerr:
        v = _verdict(VERDICT_INSUFFICIENT,
                     [e for e in (berr, oerr) if e], baseline, observed)
        # provenance fields for unreadable files
        v["baseline_collected_at_utc"] = None
        v["observed_collected_at_utc"] = None
    else:
        v = compare(baseline, observed, max_age_s=args.max_age_s)

    out = json.dumps(v, indent=2)
    if args.out:
        Path(args.out).write_text(out + "\n")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
