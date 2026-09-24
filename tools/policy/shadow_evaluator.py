#!/usr/bin/env python3
"""Phase 7C shadow-mode policy evaluator (deterministic, stdlib-only).

Consumes machine-readable Trivy JSON (authoritative policy input; the
human-readable table artifacts are presentation only) plus a previous-run
shadow/scan JSON, evaluates rules R1/R2/R3/R4 in SHADOW mode, and emits a
deterministic machine-readable verdict artifact. It NEVER fails CI: a
WOULD_FAIL verdict is still a successful, exit-code-0 run.

Rules:
  R1: CRITICAL + fix available            -> WOULD_FAIL (shadow)
      CRITICAL + no fix listed            -> visible via R3, never silent
  R2: finding identity across scans       -> NEW | PERSISTENT | RESOLVED
      (identity = cve id + pkg; severity/fix-state changes tracked as
       transitions of the same identity, never double-counted as new)
  R3: visibility channel (never blocking): no-fix CRITICAL/HIGH, active
      exceptions, expired exceptions, missing history, malformed input,
      evaluator uncertainty -> UNKNOWN records
  R4: rendered-manifest configuration observation (pod securityContext,
      container controls, resources, pinned image ref). Observation only.

LLM inference = 0. No network. Same inputs -> same verdict.
"""
import json, sys, datetime, os

SCHEMA_VERSION = 1
EVALUATOR_VERSION = "7c-shadow-1.0.0"

def finding_identity(vuln):
    """Stable identity: (cve_id, pkg_name). Pkg-scoped because fix
    availability is per (package, CVE) in Trivy JSON."""
    return f"{vuln.get('PkgName','?')}|{vuln.get('VulnerabilityID','?')}"

def normalize(scan_json):
    """Extract {(identity): {cve, pkg, severity, fixed, primary_url}} from
    Trivy JSON (Results[].Vulnerabilities[]). Returns dict + issues."""
    findings = {}
    issues = []
    data = json.loads(scan_json) if isinstance(scan_json, (str, bytes)) else scan_json
    for result in data.get("Results", []) or []:
        for v in result.get("Vulnerabilities", []) or []:
            vid = v.get("VulnerabilityID", "")
            if not vid.startswith("CVE-"):
                continue  # non-CVE advisories (e.g. ghsa) kept out of R1/R2 scope
            ident = finding_identity(v)
            rec = {
                "cve": vid,
                "pkg": v.get("PkgName", "?"),
                "severity": (v.get("Severity") or "UNKNOWN").upper(),
                "fixed": (v.get("FixedVersion") or "").strip() or None,
                "status": v.get("Status"),
                "url": v.get("PrimaryURL"),
            }
            if ident in findings and findings[ident] != rec:
                issues.append(f"conflicting duplicate identity: {ident}")
            findings[ident] = rec
    return findings, issues

def load_prev(raw):
    """Previous-run findings; None when history genuinely absent.
    MISSING HISTORY IS NOT 'NO VULNERABILITIES' — callers must treat it
    as UNKNOWN for R2."""
    if raw is None:
        return None, ["previous-run artifact unavailable (first run or retention gap)"]
    try:
        prev, issues = normalize(raw)
        return prev, issues
    except Exception as e:
        return None, [f"previous-run artifact malformed: {e}"]

def r1(findings):
    """CRITICAL-with-fix -> WOULD_FAIL; CRITICAL-no-fix -> R3-visible."""
    out = {"verdict": "PASS", "critical_with_fix": [], "critical_no_fix": []}
    for ident, f in findings.items():
        if f["severity"] == "CRITICAL":
            (out["critical_with_fix"] if f["fixed"] else out["critical_no_fix"]).append(ident)
    if out["critical_with_fix"]:
        out["verdict"] = "WOULD_FAIL"
    return out

def r2(cur, prev):
    """Persistence classification. prev=None -> all UNKNOWN(missing history)."""
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
    # persistence escalation is NOT modeled as WOULD_FAIL in shadow: R2's
    # fail semantics (N-cycle persistence) require measured data first.
    if res["persistent"]:
        res["verdict"] = "WARN"
    return res

def r3(findings, exceptions, issues):
    """Visibility records; never blocking. not-blocking != ignored."""
    now = datetime.date.today()
    recs, expired = [], []
    active_by_id = {}
    for e in exceptions:
        end = e.get("expires")
        if not end:
            expired.append({**e, "problem": "missing expiry (indefinite exceptions forbidden)"})
            continue
        (active_by_id.setdefault(e["id"], []) if datetime.date.fromisoformat(end) >= now
         else expired).append(e)
    for ident, f in findings.items():
        if f["severity"] in ("CRITICAL", "HIGH") and not f["fixed"]:
            if ident in active_by_id:
                recs.append({"identity": ident, "state": "EXCEPTION",
                             "expires": active_by_id[ident][0]["expires"]})
            else:
                recs.append({"identity": ident, "state": "VISIBLE_NO_FIX",
                             "severity": f["severity"]})
    for e in expired:
        recs.append({"identity": e["id"], "state": "EXPIRED_EXCEPTION", "detail": e})
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

def evaluate(current_path, prev_raw, rendered_path, exceptions_path, commit, timestamp):
    try:
        cur, cur_issues = normalize(open(current_path).read())
    except Exception as e:
        # malformed current input: never PASS silently
        return {"schema_version": SCHEMA_VERSION, "evaluator_version": EVALUATOR_VERSION,
                "commit": commit, "timestamp": timestamp, "verdict": "UNKNOWN",
                "error": f"current scan malformed: {e}",
                "rules": {"R1": {"verdict": "UNKNOWN"}, "R2": {"verdict": "UNKNOWN"},
                          "R3": {"verdict": "UNKNOWN", "records": [{"state": "UNKNOWN",
                                 "detail": f"current scan malformed: {e}"}]},
                          "R4": {"verdict": "UNKNOWN"}},
                "summary": {"total_findings": 0, "would_fail": 0, "warnings": 0,
                            "exceptions": 0, "expired_exceptions": 0, "unknowns": 1}}
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
            "commit": commit, "timestamp": timestamp, "verdict": verdict,
            "scan_identity": {"source": "trivy-json", "findings": len(cur)},
            "previous_scan_identity": {"available": prev is not None,
                                       "findings": len(prev) if prev is not None else None},
            "rules": {"R1": R1, "R2": R2r, "R3": R3r, "R4": R4r},
            "summary": summary}

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", required=True)
    ap.add_argument("--previous")
    ap.add_argument("--rendered", required=True)
    ap.add_argument("--exceptions", default="security-exceptions.yaml")
    ap.add_argument("--commit", default=os.environ.get("GITHUB_SHA", "local"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ts = os.environ.get("EVAL_TIMESTAMP") or datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = evaluate(a.current, open(a.previous).read() if a.previous else None,
                      a.rendered, a.exceptions, a.commit, ts)
    json.dump(result, open(a.out, "w"), indent=2, sort_keys=True)
    print(f"shadow verdict: {result['verdict']} (never blocking)")
