#!/usr/bin/env python3
"""Phase 7C shadow-mode policy evaluator (deterministic, stdlib-only).

Consumes machine-readable Trivy JSON (authoritative policy input; the
human-readable table artifacts are presentation only) plus a previous-run
shadow/scan JSON, evaluates rules R1/R2/R3/R4 in SHADOW mode (default),
and emits a deterministic machine-readable verdict artifact.

ENFORCEMENT BOUNDARY: the default mode is SHADOW and never fails CI.
An `--enforce` flag exists for the future authorization gate and is
tested by unit tests, but CI does NOT pass it. In enforce mode a FAIL
verdict exits non-zero; UNKNOWN exits non-zero too (never silently
treated as safe); shadow always exits 0.

Rules (unchanged by the P1-P5 hardening):
  R1: CRITICAL + fix available            -> WOULD_FAIL (blocking class)
      CRITICAL + no fix listed            -> visible via R3, never silent
  R2: finding identity across scans       -> NEW | PERSISTENT | RESOLVED
      (identity = PkgName|CVE; severity/fix-state/version changes tracked
       as transitions of the same identity, never double-counted as new)
  R3: visibility channel (never blocking): no-fix CRITICAL/HIGH, active
      exceptions, expired exceptions, missing history, malformed input,
      evaluator uncertainty -> UNKNOWN records
  R4: rendered platform-demo Deployment configuration observation.
      The Tier-A metrics-server evidence manifest is permanently out of
      scope.

P1 (schema validation): every scan is validated against the minimal
structure derived from the pinned scanner's real output (trivy v0.70.0
image scan: top-level Results list; per-finding VulnerabilityID, PkgName
strings; Severity in the known vocabulary or absent -> P2 handling;
FixedVersion string-or-absent). Structurally insufficient output is
NEVER evaluated as zero findings — it yields UNKNOWN (closing the
silent-PASS window found in the policy review).

P2 (severity handling): missing/malformed severity -> the finding is
retained with severity UNKNOWN and surfaced as an R3 uncertainty record;
it is never reclassified (never LOW), never skipped, and can never
satisfy R1 (a severity-less finding is not a CRITICAL), so uncertainty
cannot be converted into either PASS or a false WOULD_FAIL.

P3 (provenance): the verdict records run_id, commit, image, scanner
version, evaluation timestamp, artifact identity.

P4 (versioning): policy_version (semantic rules) is distinct from
evaluator_version (implementation) and schema_version (artifact format).

LLM inference = 0. No network. Same inputs -> same verdict.
"""
import json, sys, datetime, os, argparse

SCHEMA_VERSION = 2
EVALUATOR_VERSION = "7c-shadow-1.1.0"
POLICY_VERSION = "7c-policy-1.0.0"   # R1-R4 semantics + precedence per phase7c-policy-review.md
SEVERITY_VOCABULARY = ("UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL")
REQUIRED_VULN_FIELDS = ("VulnerabilityID", "PkgName")  # identity fields, must be non-empty strings

def validate_scan(data):
    """P1: minimal deterministic validation derived from real trivy
    v0.70.0 image-scan output (this pipeline always emits the alpine OS
    block plus a Python/library block). Returns (ok, problems). A scan
    that fails validation must never be evaluated as zero findings.
    Legitimate shapes: Vulnerabilities absent-or-null on a block means
    "no library vulns for that target" — valid ONLY when at least one
    block carries a Vulnerabilities list (any pipeline run in this
    project has always had at least one); a scan where NO block carries
    a list is a structure this pipeline has never produced -> reject."""
    problems = []
    sev_notes = []  # P2: non-fatal severity anomalies (handled in normalize)
    if not isinstance(data, dict):
        return False, ["top-level JSON is not an object"]
    if "Results" not in data:
        # Real scans always carry Results (even clean ones). Absent
        # Results = insufficient, never "zero findings".
        return False, ["missing Results collection (structurally insufficient scan)"]
    results = data["Results"]
    if not isinstance(results, list):
        return False, ["Results is not a list"]
    blocks_with_vuln_list = 0
    for i, result in enumerate(results):
        if not isinstance(result, dict):
            problems.append(f"Results[{i}] is not an object")
            continue
        vulns = result.get("Vulnerabilities")
        if vulns is None:
            continue  # legitimate: a target with no library vulns
        if not isinstance(vulns, list):
            problems.append(f"Results[{i}].Vulnerabilities is not a list")
            continue
        blocks_with_vuln_list += 1
        for j, v in enumerate(vulns):
            if not isinstance(v, dict):
                problems.append(f"Vulnerability entry [{i}][{j}] is not an object")
                continue
            for f in REQUIRED_VULN_FIELDS:
                val = v.get(f)
                if not isinstance(val, str) or not val.strip():
                    problems.append(f"Vulnerability entry [{i}][{j}] missing/invalid {f}")
            sev = v.get("Severity")
            if sev is not None and (not isinstance(sev, str) or sev.upper() not in SEVERITY_VOCABULARY):
                # P2: malformed severity is NON-fatal — the finding is
                # retained with severity UNKNOWN and surfaced via R3;
                # invalidating the whole scan here would discard good
                # findings alongside one bad field.
                sev_notes.append(f"Vulnerability [{i}][{j}] has malformed Severity: {sev!r}")
            fx = v.get("FixedVersion")
            if fx is not None and not isinstance(fx, str):
                problems.append(f"Vulnerability [{i}][{j}] has non-string FixedVersion")
    if not problems and blocks_with_vuln_list == 0:
        # covers BOTH zero blocks and all-null blocks: never-seen structure
        # for this pipeline; empty scan is not distinguishable from
        # scan insufficiency (and silently deleting the previous
        # inventory as "resolved" would be a silent-PASS path).
        return False, ["no Results block carries a Vulnerabilities collection "
                       "(never-seen structure for this pipeline; empty scan is "
                       "not distinguishable from scan insufficiency)"]
    # Any per-entry structural problem (missing identity, wrong types)
    # invalidates the scan — never a silent skip. Severity anomalies are
    # P2 non-fatal notes: passed back so normalize can retain the finding
    # as UNKNOWN and surface it via R3.
    return (not problems), problems + sev_notes

def finding_identity(vuln):
    """Stable identity: (pkg_name, cve_id). Pkg-scoped because fix
    availability is per (package, CVE) in Trivy JSON."""
    return f"{vuln.get('PkgName','?')}|{vuln.get('VulnerabilityID','?')}"

def normalize(scan_json):
    """Extract {(identity): {cve, pkg, severity, fixed, ...}} from Trivy
    JSON. Returns (findings, issues, schema_ok). Raises on unparseable
    JSON; structural insufficiency is reported via schema_ok=False."""
    findings, issues = {}, []
    data = json.loads(scan_json) if isinstance(scan_json, (str, bytes)) else scan_json
    ok, problems = validate_scan(data)
    if not ok:
        return {}, problems, False
    # P2: non-fatal severity notes flow into R3 visibility (issues)
    issues.extend(p for p in problems if "malformed Severity" in p)
    for result in data["Results"]:
        for v in result.get("Vulnerabilities", []) or []:
            vid = v.get("VulnerabilityID", "")
            if not vid.startswith("CVE-"):
                continue  # non-CVE advisories (e.g. ghsa) kept out of R1/R2 scope
            sev_raw = v.get("Severity")
            if sev_raw is None or (isinstance(sev_raw, str) and not sev_raw.strip()):
                sev = "UNKNOWN"
                issues.append(f"severity absent on {finding_identity(v)} (P2: retained as UNKNOWN, visible via R3)")
            elif isinstance(sev_raw, str) and sev_raw.upper() in SEVERITY_VOCABULARY:
                sev = sev_raw.upper()
                if sev_raw != sev:
                    issues.append(f"non-canonical severity casing on {finding_identity(v)}: {sev_raw!r}")
            else:
                sev = "UNKNOWN"
                issues.append(f"malformed severity on {finding_identity(v)}: {sev_raw!r} (P2: retained as UNKNOWN)")
            ident = finding_identity(v)
            rec = {
                "cve": vid,
                "pkg": v.get("PkgName", "?"),
                "severity": sev,
                "fixed": (v.get("FixedVersion") or "").strip() or None if isinstance(v.get("FixedVersion"), str) else None,
                "status": v.get("Status"),
                "url": v.get("PrimaryURL"),
            }
            if ident in findings and findings[ident] != rec:
                issues.append(f"conflicting duplicate identity: {ident}")
            findings[ident] = rec
    return findings, issues, True

def load_prev(raw):
    """Previous-run findings; None when history genuinely absent.
    MISSING HISTORY IS NOT 'NO VULNERABILITIES' — callers must treat it
    as UNKNOWN for R2. `raw` may be a path (missing file -> None) or JSON
    text. A previous artifact failing P1 validation is history-missing
    plus an explicit issue, never an empty inventory."""
    if raw is None:
        return None, ["previous-run artifact unavailable (first run or retention gap)"]
    if isinstance(raw, (str, bytes)) and raw.strip().endswith(".json"):
        if not os.path.exists(raw):
            return None, ["previous-run artifact unavailable (first run or retention gap)"]
        try:
            raw = open(raw).read()
        except Exception as e:
            return None, [f"previous-run artifact unreadable: {e}"]
    try:
        prev, issues, ok = normalize(raw)
        if not ok:
            return None, [f"previous-run artifact structurally insufficient: {'; '.join(issues)}"]
        return prev, issues
    except Exception as e:
        return None, [f"previous-run artifact malformed: {e}"]

def r1(findings):
    """CRITICAL-with-fix -> WOULD_FAIL; CRITICAL-no-fix -> R3-visible.
    Severity UNKNOWN can never satisfy this rule (P2), so uncertainty
    can never fabricate a blocking condition either."""
    out = {"verdict": "PASS", "critical_with_fix": [], "critical_no_fix": []}
    for ident, f in findings.items():
        if f["severity"] == "CRITICAL":
            (out["critical_with_fix"] if f["fixed"] else out["critical_no_fix"]).append(ident)
    if out["critical_with_fix"]:
        out["verdict"] = "WOULD_FAIL"
    return out

def r2(cur, prev):
    """Persistence classification. prev=None -> UNKNOWN (missing history)."""
    res = {"verdict": "PASS", "new": [], "persistent": [], "resolved": [],
           "changed": [], "history_available": prev is not None}
    if prev is None:
        res["verdict"] = "UNKNOWN"
        return res
    for ident, f in cur.items():
        if ident not in prev:
            res["new"].append(ident)
        else:
            p = prev[ident]
            if p["severity"] != f["severity"]:
                res["changed"].append({"identity": ident, "severity": f"{p['severity']}->{f['severity']}"})
            if p["fixed"] != f["fixed"]:
                res["changed"].append({"identity": ident, "fix": f"{p['fixed']}->{f['fixed']}"})
            res["persistent"].append(ident)
    for ident in prev:
        if ident not in cur:
            res["resolved"].append(ident)
    # persistence escalation is NOT modeled as WOULD_FAIL: R2 stays
    # observational (WARN-only) per the policy review contract.
    if res["persistent"]:
        res["verdict"] = "WARN"
    return res

def parse_exceptions(exceptions, issues):
    """Classify exception entries. Returns (active_by_id, expired).
    Malformed entries are treated as expired-equivalent (never silently
    tolerant): missing expiry, non-dict, missing id, or unparseable date."""
    now = datetime.date.today()
    active_by_id, expired = {}, []
    for e in exceptions:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e.get("id").strip():
            expired.append({"entry": e, "problem": "malformed exception entry (treated as expired-equivalent)"})
            continue
        end = e.get("expires")
        try:
            if not end:
                raise ValueError("missing expiry")
            d = datetime.date.fromisoformat(str(end))
        except (ValueError, TypeError):
            expired.append({**e, "problem": "missing/unparseable expiry (indefinite exceptions forbidden)"})
            continue
        (active_by_id.setdefault(e["id"], []) if d >= now else expired).append(e)
    return active_by_id, expired

def r3(findings, exceptions, issues):
    """Visibility records; never blocking. not-blocking != ignored."""
    active_by_id, expired = parse_exceptions(exceptions, issues)
    recs = []
    for ident, f in findings.items():
        if f["severity"] in ("CRITICAL", "HIGH") and not f["fixed"]:
            if ident in active_by_id:
                recs.append({"identity": ident, "state": "EXCEPTION",
                             "expires": active_by_id[ident][0]["expires"]})
            else:
                recs.append({"identity": ident, "state": "VISIBLE_NO_FIX",
                             "severity": f["severity"]})
        elif f["severity"] == "UNKNOWN":
            recs.append({"identity": ident, "state": "UNKNOWN",
                         "detail": "severity absent/malformed (P2): finding retained, policy impact uncertain"})
    for e in expired:
        recs.append({"identity": e.get("id", "?"), "state": "EXPIRED_EXCEPTION", "detail": e})
    for msg in issues:
        recs.append({"state": "UNKNOWN", "detail": msg})
    return {"verdict": "WARN" if recs else "PASS", "records": recs}

def r4(rendered_path):
    """Observation of rendered platform-demo Deployment. Scoped explicitly:
    only the platform-demo chart render — the Tier-A metrics-server
    evidence manifest is history and must never gate anything."""
    checks = {
        "pod_runAsNonRoot": None, "pod_runAsUser": None,
        "pod_seccompProfile": None,
        "ctr_allowPrivilegeEscalation": None, "ctr_readOnlyRootFilesystem": None,
        "ctr_runAsNonRoot": None, "ctr_runAsUser": None,
        "resources_configured": None, "image_pinned": None,
    }
    details = {}
    try:
        docs = [d for d in open(rendered_path).read().split("\n---")]
    except FileNotFoundError:
        return {"verdict": "UNKNOWN", "checks": checks,
                "detail": "rendered manifest not found (render step must run first)"}
    dep = next((d for d in docs if d.strip() and "kind: Deployment" in d), None)
    if dep is None:
        return {"verdict": "UNKNOWN", "checks": checks, "detail": "no Deployment document"}
    try:
        import yaml
        spec = yaml.safe_load(dep)["spec"]["template"]["spec"]
    except Exception as e:
        return {"verdict": "UNKNOWN", "checks": checks, "detail": f"yaml parse: {e}"}
    pod_sc = spec.get("securityContext") or {}
    checks["pod_runAsNonRoot"] = pod_sc.get("runAsNonRoot") is True
    checks["pod_runAsUser"] = pod_sc.get("runAsUser") == 65534
    checks["pod_seccompProfile"] = ((pod_sc.get("seccompProfile") or {}).get("type")) == "RuntimeDefault"
    c = (spec.get("containers") or [{}])[0]
    c_sc = c.get("securityContext") or {}
    checks["ctr_allowPrivilegeEscalation"] = c_sc.get("allowPrivilegeEscalation") is False
    checks["ctr_readOnlyRootFilesystem"] = c_sc.get("readOnlyRootFilesystem") is True
    checks["ctr_runAsNonRoot"] = c_sc.get("runAsNonRoot") is True
    checks["ctr_runAsUser"] = c_sc.get("runAsUser") == 65534
    res = c.get("resources") or {}
    checks["resources_configured"] = bool(res.get("requests") and res.get("limits"))
    img = c.get("image", "")
    checks["image_pinned"] = (":" in img.split("/")[-1]) and not img.rstrip().endswith(":latest")
    details["image"] = img
    failed = [k for k, v in checks.items() if v is not True]
    return {"verdict": "WOULD_FAIL" if failed else "PASS",
            "checks": checks, **details}

def evaluate(current_path, prev_raw, rendered_path, exceptions_path, commit, timestamp,
             run_id=None, image=None, scanner_version=None):
    """Evaluate one cycle. Provenance (P3): run_id/image/scanner_version
    are recorded when the caller supplies them; absent provenance is
    recorded as null — never fabricated."""
    provenance = {"run_id": run_id, "image": image, "scanner_version": scanner_version}
    try:
        raw = open(current_path).read()
        cur, cur_issues, schema_ok = normalize(raw)
        if not schema_ok:
            # P1: structurally insufficient scan -> explicit UNKNOWN, never
            # evaluated as zero findings (silent-PASS window closed).
            detail = "; ".join(cur_issues) or "structurally insufficient scan"
            return _unknown_result(commit, timestamp, provenance,
                                   f"current scan structurally insufficient: {detail}")
    except json.JSONDecodeError as e:
        return _unknown_result(commit, timestamp, provenance, f"current scan malformed JSON: {e}")
    except Exception as e:
        return _unknown_result(commit, timestamp, provenance, f"current scan unreadable: {e}")
    prev, prev_issues = load_prev(prev_raw)
    exceptions = []
    if exceptions_path and os.path.exists(exceptions_path):
        try:
            exceptions = json.load(open(exceptions_path)).get("exceptions", [])
        except Exception as e:
            prev_issues.append(f"exceptions file malformed: {e}")
    R1 = r1(cur); R2r = r2(cur, prev)
    R3r = r3(cur, exceptions, cur_issues + prev_issues)
    R4r = r4(rendered_path)
    verdict = "WOULD_FAIL" if R1["verdict"] == "WOULD_FAIL" or R4r["verdict"] == "WOULD_FAIL" else \
              ("UNKNOWN" if "UNKNOWN" in (R2r["verdict"], R3r["verdict"], R4r["verdict"]) else \
               ("WARN" if "WARN" in (R2r["verdict"], R3r["verdict"], R4r["verdict"]) else "PASS"))
    summary = {
        "total_findings": len(cur),
        "would_fail": len(R1["critical_with_fix"]),
        "warnings": len(R3r["records"]),
        "exceptions": sum(1 for r in R3r["records"] if r.get("state") == "EXCEPTION"),
        "expired_exceptions": sum(1 for r in R3r["records"] if r.get("state") == "EXPIRED_EXCEPTION"),
        "unknowns": sum(1 for r in R3r["records"] if r.get("state") == "UNKNOWN") + (1 if R2r["verdict"] == "UNKNOWN" else 0),
        "new": len(R2r["new"]), "persistent": len(R2r["persistent"]),
        "resolved": len(R2r["resolved"]), "r4_failures": 0 if R4r["verdict"] == "PASS" else 1,
    }
    return {"schema_version": SCHEMA_VERSION, "evaluator_version": EVALUATOR_VERSION,
            "policy_version": POLICY_VERSION,
            "commit": commit, "timestamp": timestamp, "verdict": verdict,
            "provenance": provenance,
            "scan_identity": {"source": "trivy-json", "findings": len(cur),
                              "schema_validated": True},
            "previous_scan_identity": {"available": prev is not None,
                                       "findings": len(prev) if prev is not None else None},
            "rules": {"R1": R1, "R2": R2r, "R3": R3r, "R4": R4r},
            "summary": summary}

def _unknown_result(commit, timestamp, provenance, error):
    """Canonical UNKNOWN result: never PASS, error always recorded."""
    return {"schema_version": SCHEMA_VERSION, "evaluator_version": EVALUATOR_VERSION,
            "policy_version": POLICY_VERSION,
            "commit": commit, "timestamp": timestamp, "verdict": "UNKNOWN",
            "provenance": provenance,
            "error": error,
            "rules": {"R1": {"verdict": "UNKNOWN"}, "R2": {"verdict": "UNKNOWN"},
                      "R3": {"verdict": "UNKNOWN", "records": [{"state": "UNKNOWN",
                             "detail": error}]},
                      "R4": {"verdict": "UNKNOWN"}},
            "summary": {"total_findings": 0, "would_fail": 0, "warnings": 0,
                        "exceptions": 0, "expired_exceptions": 0, "unknowns": 1,
                        "new": 0, "persistent": 0, "resolved": 0, "r4_failures": 0}}

def exit_code_for(verdict, enforce):
    """P5: deterministic mode semantics. Shadow: always 0 (WOULD_FAIL is
    still a successful run). Enforce (future, not activated in CI): FAIL
    -> non-zero; UNKNOWN -> non-zero (never silently treated as safe,
    per policy review); WARN/PASS -> 0."""
    if not enforce:
        return 0
    return 0 if verdict in ("PASS", "WARN", "EXCEPTION") else 1

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", required=True)
    ap.add_argument("--previous")
    ap.add_argument("--rendered", required=True)
    ap.add_argument("--exceptions", default="tools/policy/security-exceptions.json")
    ap.add_argument("--commit", default=os.environ.get("GITHUB_SHA", "local"))
    ap.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID"))
    ap.add_argument("--image", default=os.environ.get("POLICY_IMAGE_REF"))
    ap.add_argument("--scanner-version", default=os.environ.get("POLICY_SCANNER_VERSION"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--enforce", action="store_true",
                    help="FUTURE gate (not used by CI): exit non-zero on FAIL/UNKNOWN. "
                         "Default (and CI) is shadow mode: always exit 0.")
    a = ap.parse_args()
    ts = os.environ.get("EVAL_TIMESTAMP") or datetime.datetime.now(datetime.timezone.utc).isoformat()
    # Pass the PATH, not an open handle: a missing previous file is a normal
    # first-run/retention-gap condition and must reach evaluate() as such
    # (recorded as UNKNOWN history), never raise here (7C CI failure #1).
    result = evaluate(a.current, a.previous, a.rendered, a.exceptions, a.commit, ts,
                      run_id=a.run_id, image=a.image, scanner_version=a.scanner_version)
    json.dump(result, open(a.out, "w"), indent=2, sort_keys=True)
    code = exit_code_for(result["verdict"], a.enforce)
    mode = "ENFORCE" if a.enforce else "shadow"
    print(f"{mode} verdict: {result['verdict']} -> exit {code}")
    sys.exit(code)
