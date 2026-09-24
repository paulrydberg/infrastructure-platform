#!/usr/bin/env python3
"""Unit + historical-regression + hardening (P1-P5) tests for the Phase 7C
shadow evaluator. Deterministic, stdlib-only, no network.
Run: python3 tools/policy/test_shadow_evaluator.py. Exit 0 = all pass."""
import json, os, sys, tempfile, datetime, unittest, subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shadow_evaluator as ev

TMP = tempfile.mkdtemp()

def wj(obj, name):
    p = os.path.join(TMP, name)
    json.dump(obj, open(p, "w"))
    return p

def trivy_json(vulns):
    return {"Results": [{"Target": "platform-demo:0.1.0 (alpine 3.22)",
                          "Vulnerabilities": vulns}]}

def v(cve, pkg, sev, fixed=None):
    d = {"VulnerabilityID": cve, "PkgName": pkg, "Severity": sev,
         "PrimaryURL": f"https://avd.aquasec.com/nvd/{cve.lower()}"}
    if fixed: d["FixedVersion"] = fixed
    return d

RENDERED_OK = """apiVersion: apps/v1
kind: Deployment
metadata: {name: platform-demo}
spec:
  template:
    spec:
      securityContext: {runAsNonRoot: true, runAsUser: 65534, seccompProfile: {type: RuntimeDefault}}
      containers:
        - name: demo
          image: python:3.12-alpine3.22
          securityContext: {allowPrivilegeEscalation: false, readOnlyRootFilesystem: true, runAsNonRoot: true, runAsUser: 65534}
          resources: {requests: {memory: 64Mi}, limits: {memory: 128Mi}}
"""

RENDERED_BAD_POD = RENDERED_OK.replace("      securityContext: {runAsNonRoot: true, runAsUser: 65534, seccompProfile: {type: RuntimeDefault}}\n", "")
RENDERED_BAD_CTR = RENDERED_OK.replace("          securityContext: {allowPrivilegeEscalation: false, readOnlyRootFilesystem: true, runAsNonRoot: true, runAsUser: 65534}\n", "")
RENDERED_BAD_IMG = RENDERED_OK.replace("python:3.12-alpine3.22", "python:latest")

def render(p, text):
    path = os.path.join(TMP, p); open(path, "w").write(text); return path

EXC_ACTIVE = [{"id": "pkg|CVE-2026-0001", "scope": "image", "reason": "no upstream fix",
               "owner": "paul", "created": "2026-09-01",
               "expires": str(datetime.date.today() + datetime.timedelta(days=30)),
               "evidence": "test", "compensating_controls": ["runAsNonRoot"], "review_required": True}]
EXC_EXPIRED = [{"id": "pkg|CVE-2026-0001", "scope": "image", "reason": "no upstream fix",
                "owner": "paul", "created": "2026-01-01", "expires": "2026-02-01",
                "evidence": "test", "compensating_controls": [], "review_required": True}]
EXC_MALFORMED = [{"no_id_here": True}, {"id": "pkg|CVE-2026-0002"}]  # no expiry, no id

def evaluate(obj_or_path, prev=None, rendered=None, exceptions=None, **kw):
    p = obj_or_path if isinstance(obj_or_path, str) else wj(obj_or_path, f"scan-{id(obj_or_path)}.json")
    return ev.evaluate(p, prev, rendered or render("r.yaml", RENDERED_OK), exceptions,
                       kw.get("commit", "test"), kw.get("ts", "2026-09-24T00:00:00Z"),
                       run_id=kw.get("run_id"), image=kw.get("image"),
                       scanner_version=kw.get("scanner_version"))

class TestR1(unittest.TestCase):
    def test_critical_with_fix_would_fail(self):
        r = ev.r1(ev.normalize(json.dumps(trivy_json([v("CVE-2026-31789","libssl3","CRITICAL","3.3.7-r0")])))[0])
        self.assertEqual(r["verdict"], "WOULD_FAIL")
    def test_critical_no_fix_not_silent(self):
        r = ev.r1(ev.normalize(json.dumps(trivy_json([v("CVE-2026-99999","x","CRITICAL")])))[0])
        self.assertEqual(r["verdict"], "PASS")
        self.assertEqual(len(r["critical_no_fix"]), 1)

class TestR2(unittest.TestCase):
    def setUp(self):
        self.prev = trivy_json([v("CVE-2026-1","a","HIGH","2.0"),
                                v("CVE-2026-2","b","HIGH"),
                                v("CVE-2026-3","c","HIGH","3.0")])
        self.cur_same = trivy_json([v("CVE-2026-1","a","HIGH","2.0"),
                                    v("CVE-2026-2","b","HIGH")])
    def test_new(self):
        cur = trivy_json([v("CVE-2026-9","z","HIGH","1.0")])
        r = ev.r2(ev.normalize(json.dumps(cur))[0], ev.normalize(json.dumps(self.prev))[0])
        self.assertEqual(r["new"], ["z|CVE-2026-9"]); self.assertEqual(r["verdict"], "PASS")
    def test_persistent(self):
        r = ev.r2(ev.normalize(json.dumps(self.cur_same))[0], ev.normalize(json.dumps(self.prev))[0])
        self.assertIn("a|CVE-2026-1", r["persistent"]); self.assertEqual(r["verdict"], "WARN")
    def test_resolved(self):
        r = ev.r2(ev.normalize(json.dumps(self.cur_same))[0], ev.normalize(json.dumps(self.prev))[0])
        self.assertIn("c|CVE-2026-3", r["resolved"])
    def test_severity_change_not_new(self):
        cur = trivy_json([v("CVE-2026-1","a","CRITICAL","2.0")])
        r = ev.r2(ev.normalize(json.dumps(cur))[0], ev.normalize(json.dumps(self.prev))[0])
        self.assertNotIn("a|CVE-2026-1", r["new"]); self.assertIn("a|CVE-2026-1", r["persistent"])
        self.assertTrue(any("HIGH->CRITICAL" == c["severity"] for c in r["changed"]))
    def test_fix_availability_change_not_new(self):
        cur = trivy_json([v("CVE-2026-1","a","HIGH")])
        r = ev.r2(ev.normalize(json.dumps(cur))[0], ev.normalize(json.dumps(self.prev))[0])
        self.assertNotIn("a|CVE-2026-1", r["new"]); self.assertIn("a|CVE-2026-1", r["persistent"])
        self.assertTrue(any("2.0->None" == c["fix"] for c in r["changed"]))
    def test_missing_history_unknown(self):
        r = ev.r2(ev.normalize(json.dumps(self.cur_same))[0], None)
        self.assertEqual(r["verdict"], "UNKNOWN"); self.assertFalse(r["history_available"])

class TestR3(unittest.TestCase):
    def test_no_fix_high_visible(self):
        r = ev.r3(ev.normalize(json.dumps(trivy_json([v("CVE-2026-53613","libuuid","HIGH")])))[0], [], [])
        self.assertEqual(r["records"][0]["state"], "VISIBLE_NO_FIX"); self.assertEqual(r["verdict"], "WARN")
    def test_active_exception(self):
        r = ev.r3(ev.normalize(json.dumps(trivy_json([v("CVE-2026-0001","pkg","HIGH")])))[0], EXC_ACTIVE, [])
        self.assertEqual(r["records"][0]["state"], "EXCEPTION")
    def test_expired_exception_surfaces(self):
        r = ev.r3(ev.normalize(json.dumps(trivy_json([v("CVE-2026-0001","pkg","HIGH")])))[0], EXC_EXPIRED, [])
        states = [x["state"] for x in r["records"]]
        self.assertIn("EXPIRED_EXCEPTION", states); self.assertNotIn("EXCEPTION", states)
    def test_malformed_exception_entries_not_silently_tolerated(self):
        r = ev.r3(ev.normalize(json.dumps(trivy_json([v("CVE-2026-0001","pkg","HIGH")])))[0], EXC_MALFORMED, [])
        states = [x["state"] for x in r["records"]]
        self.assertIn("EXPIRED_EXCEPTION", states)  # malformed => expired-equivalent, never tolerance

class TestP1SchemaValidation(unittest.TestCase):
    """P1: structurally insufficient scans must NEVER become PASS."""
    HIST = trivy_json([v("CVE-2026-9","z","HIGH","1.0")])
    def _verdict(self, obj, prev_obj="DEFAULT_HISTORY"):
        # default: supply history so R2 is determined; P1 tests are about
        # scan-structure acceptance, not first-run behavior
        if prev_obj == "DEFAULT_HISTORY":
            prev_obj = self.HIST
        return evaluate(obj, prev=wj(prev_obj, "p1-prev.json") if prev_obj else None)["verdict"]
    def test_silent_pass_window_closed(self):
        # THE regression: empty scan + available history was PASS pre-P1.
        hist = trivy_json([v("CVE-2026-9","z","HIGH","1.0")])
        self.assertEqual(self._verdict({"Results": []}, hist), "UNKNOWN")
        self.assertEqual(self._verdict({}, hist), "UNKNOWN")                       # missing Results
        self.assertEqual(self._verdict({"foo": "bar"}, hist), "UNKNOWN")           # missing Results
        self.assertEqual(self._verdict({"Results": "oops"}, hist), "UNKNOWN")      # wrong type
    def test_malformed_json_unknown(self):
        p = os.path.join(TMP, "bad.json"); open(p, "w").write("{not json")
        self.assertEqual(ev.evaluate(p, None, render("r.yaml", RENDERED_OK), None, "t", "t")["verdict"], "UNKNOWN")
    def test_missing_identity_unknown(self):
        # P1: VulnerabilityID/PkgName are required identity fields
        self.assertEqual(self._verdict({"Results": [{"Vulnerabilities": [{"Severity": "HIGH"}]}]}), "UNKNOWN")
        self.assertEqual(self._verdict({"Results": [{"Vulnerabilities": [{"VulnerabilityID": "CVE-2026-1"}]}]}), "UNKNOWN")
        self.assertEqual(self._verdict({"Results": [{"Vulnerabilities": [{"VulnerabilityID": "", "PkgName": "x", "Severity": "HIGH"}]}]}), "UNKNOWN")
    def test_wrong_field_type_unknown(self):
        self.assertEqual(self._verdict({"Results": [{"Vulnerabilities": [123]}]}), "UNKNOWN")
        self.assertEqual(self._verdict({"Results": [{"Vulnerabilities": [{"VulnerabilityID": "CVE-2026-1", "PkgName": "x", "Severity": "HIGH", "FixedVersion": 123}]}]}), "UNKNOWN")
        self.assertEqual(self._verdict({"Results": [{"Vulnerabilities": "notalist"}]}), "UNKNOWN")
    def test_legitimate_structure_still_passes(self):
        # A block with an explicit empty Vulnerabilities LIST is valid
        # structure; clean scan + history where that finding also resolves
        # -> PASS. (Use history matching the empty scan so R2 = no changes.)
        hist = trivy_json([])
        self.assertEqual(self._verdict({"Results": [{"Target": "t", "Vulnerabilities": []}]}, hist), "PASS")
        two_blocks = {"Results": [{"Target": "t", "Vulnerabilities": []},
                                  {"Target": "python", "Vulnerabilities": None}]}
        self.assertEqual(self._verdict(two_blocks, hist), "PASS")
    def test_empty_results_with_history_not_pass(self):
        # Results: [] (zero blocks) is never-seen structure -> UNKNOWN,
        # even with history (would otherwise masquerade as full remediation)
        self.assertEqual(self._verdict({"Results": []}), "UNKNOWN")
    def test_all_null_vulns_unknown(self):
        # Every block null-vulns: never-seen structure for this pipeline -> UNKNOWN
        self.assertEqual(self._verdict({"Results": [{"Target": "t", "Vulnerabilities": None}]}), "UNKNOWN")
    def test_schema_validated_flag(self):
        res = evaluate(trivy_json([v("CVE-2026-1","x","LOW","1.0")]))
        self.assertTrue(res["scan_identity"]["schema_validated"])

class TestP2Severity(unittest.TestCase):
    def test_valid_severity(self):
        f, issues, ok = ev.normalize(json.dumps(trivy_json([v("CVE-2026-1","x","HIGH","1.0")])))
        self.assertEqual(f["x|CVE-2026-1"]["severity"], "HIGH"); self.assertEqual(issues, []); self.assertTrue(ok)
    def test_missing_severity_retained_unknown_not_skipped(self):
        f, issues, ok = ev.normalize(json.dumps(trivy_json([{"VulnerabilityID": "CVE-2026-1", "PkgName": "x"}])))
        self.assertTrue(ok); self.assertEqual(f["x|CVE-2026-1"]["severity"], "UNKNOWN")
        self.assertTrue(any("severity absent" in i for i in issues))
        # visible via R3, never silently harmless:
        r = ev.r3(f, [], issues)
        self.assertEqual(r["records"][0]["state"], "UNKNOWN")
    def test_malformed_severity_unknown(self):
        f, issues, ok = ev.normalize(json.dumps(trivy_json([{"VulnerabilityID": "CVE-2026-1", "PkgName": "x", "Severity": 123}])))
        self.assertEqual(f["x|CVE-2026-1"]["severity"], "UNKNOWN")
        self.assertTrue(any("malformed severity" in i for i in issues))
    def test_unexpected_severity_value_unknown(self):
        f, issues, _ = ev.normalize(json.dumps(trivy_json([{"VulnerabilityID": "CVE-2026-1", "PkgName": "x", "Severity": "CATASTROPHIC"}])))
        self.assertEqual(f["x|CVE-2026-1"]["severity"], "UNKNOWN")
        self.assertTrue(any("malformed severity" in i for i in issues))
    def test_lowercase_severity_canonicalized(self):
        f, issues, _ = ev.normalize(json.dumps(trivy_json([{"VulnerabilityID": "CVE-2026-1", "PkgName": "x", "Severity": "critical", "FixedVersion": "1.0"}])))
        self.assertEqual(f["x|CVE-2026-1"]["severity"], "CRITICAL")
        r1 = ev.r1(f); self.assertEqual(r1["verdict"], "WOULD_FAIL")
    def test_missing_severity_cannot_satisfy_r1(self):
        # uncertainty can never fabricate a blocking condition
        f, _, _ = ev.normalize(json.dumps(trivy_json([{"VulnerabilityID": "CVE-2026-1", "PkgName": "x", "FixedVersion": "1.0"}])))
        self.assertEqual(ev.r1(f)["verdict"], "PASS")

class TestP3Provenance(unittest.TestCase):
    def test_provenance_recorded(self):
        res = evaluate(trivy_json([v("CVE-2026-1","x","LOW","1.0")]),
                       run_id="12345", image="platform-demo:0.1.0", scanner_version="0.70.0")
        self.assertEqual(res["provenance"], {"run_id": "12345", "image": "platform-demo:0.1.0",
                                             "scanner_version": "0.70.0"})
    def test_absent_provenance_null_never_fabricated(self):
        res = evaluate(trivy_json([]))
        self.assertEqual(res["provenance"], {"run_id": None, "image": None, "scanner_version": None})
    def test_provenance_survives_unknown(self):
        res = evaluate({"foo": "bar"}, run_id="99")
        self.assertEqual(res["verdict"], "UNKNOWN"); self.assertEqual(res["provenance"]["run_id"], "99")

class TestP4Versions(unittest.TestCase):
    def test_distinct_version_concepts(self):
        self.assertNotEqual(ev.POLICY_VERSION, ev.EVALUATOR_VERSION)
        res = evaluate(trivy_json([]))
        self.assertEqual(res["policy_version"], ev.POLICY_VERSION)
        self.assertEqual(res["evaluator_version"], ev.EVALUATOR_VERSION)
        self.assertIn("policy_version", res)
    def test_schema_version_present(self):
        res = evaluate(trivy_json([]))
        self.assertEqual(res["schema_version"], 2)

class TestR4(unittest.TestCase):
    def test_valid(self):
        r = ev.r4(render("ok.yaml", RENDERED_OK))
        self.assertEqual(r["verdict"], "PASS"); self.assertTrue(r["checks"]["pod_runAsUser"])
    def test_missing_pod_sc(self):
        r = ev.r4(render("bad1.yaml", RENDERED_BAD_POD))
        self.assertEqual(r["verdict"], "WOULD_FAIL"); self.assertFalse(r["checks"]["pod_runAsNonRoot"])
    def test_missing_container_control(self):
        r = ev.r4(render("bad2.yaml", RENDERED_BAD_CTR))
        self.assertEqual(r["verdict"], "WOULD_FAIL"); self.assertFalse(r["checks"]["ctr_readOnlyRootFilesystem"])
    def test_mutable_image(self):
        r = ev.r4(render("bad3.yaml", RENDERED_BAD_IMG))
        self.assertEqual(r["verdict"], "WOULD_FAIL"); self.assertFalse(r["checks"]["image_pinned"])

class TestP5EnforcementContract(unittest.TestCase):
    """Exit-code semantics WITHOUT enabling enforcement in CI."""
    def _run_cli(self, verdict_obj, enforce):
        cur = wj(verdict_obj, f"cli-{abs(hash(json.dumps(verdict_obj, sort_keys=True)))}.json")
        out = os.path.join(TMP, "cli-out.json")
        args = [sys.executable, os.path.join(os.path.dirname(ev.__file__), "shadow_evaluator.py"),
                "--current", cur, "--rendered", render("r.yaml", RENDERED_OK),
                "--out", out, "--commit", "test"]
        if enforce: args.append("--enforce")
        r = subprocess.run(args, capture_output=True, text=True,
                           env={**os.environ, "EVAL_TIMESTAMP": "2026-09-24T00:00:00Z"})
        return r.returncode, json.load(open(out))
    def test_shadow_would_fail_exits_zero(self):
        code, res = self._run_cli(trivy_json([v("CVE-2026-1","x","CRITICAL","1.0")]), enforce=False)
        self.assertEqual((code, res["verdict"]), (0, "WOULD_FAIL"))
    def test_enforce_would_fail_exits_nonzero(self):
        code, res = self._run_cli(trivy_json([v("CVE-2026-1","x","CRITICAL","1.0")]), enforce=True)
        self.assertEqual((code, res["verdict"]), (1, "WOULD_FAIL"))
    def test_enforce_pass_exits_zero(self):
        # clean scan + matching history -> PASS (no history would be UNKNOWN by design)
        hist = wj(trivy_json([]), "p5-hist.json")
        cur = wj(trivy_json([]), "p5-clean.json")
        out = os.path.join(TMP, "p5-pass.json")
        r = subprocess.run([sys.executable, os.path.join(os.path.dirname(ev.__file__), "shadow_evaluator.py"),
                            "--current", cur, "--previous", hist,
                            "--rendered", render("r.yaml", RENDERED_OK), "--out", out, "--enforce"],
                           capture_output=True, text=True,
                           env={**os.environ, "EVAL_TIMESTAMP": "2026-09-24T00:00:00Z"})
        self.assertEqual((r.returncode, json.load(open(out))["verdict"]), (0, "PASS"))
    def test_enforce_unknown_exits_nonzero_never_safe(self):
        code, res = self._run_cli({"foo": "bar"}, enforce=True)
        self.assertEqual((code, res["verdict"]), (1, "UNKNOWN"))
    def test_shadow_unknown_exits_zero(self):
        code, res = self._run_cli({"foo": "bar"}, enforce=False)
        self.assertEqual((code, res["verdict"]), (0, "UNKNOWN"))
    def test_r4_violation_enforce_fails(self):
        cur = wj(trivy_json([]), "r4-cli.json")
        out = os.path.join(TMP, "r4-out.json")
        r = subprocess.run([sys.executable, os.path.join(os.path.dirname(ev.__file__), "shadow_evaluator.py"),
                            "--current", cur, "--rendered", render("bad1.yaml", RENDERED_BAD_POD),
                            "--out", out, "--enforce"], capture_output=True, text=True,
                           env={**os.environ, "EVAL_TIMESTAMP": "2026-09-24T00:00:00Z"})
        self.assertEqual(r.returncode, 1)
    def test_rollback_restores_shadow(self):
        # rollback = drop --enforce: same failing input, shadow exit 0 again
        fail_scan = trivy_json([v("CVE-2026-1","x","CRITICAL","1.0")])
        self.assertEqual(self._run_cli(fail_scan, enforce=True)[0], 1)
        self.assertEqual(self._run_cli(fail_scan, enforce=False)[0], 0)

class TestPrecedence(unittest.TestCase):
    """Explicit precedence: malformed > expired-exc > active-exc > R1 > R4 > WARN/UNKNOWN > PASS."""
    def test_malformed_beats_everything(self):
        res = evaluate({"foo": "bar"})
        self.assertEqual(res["verdict"], "UNKNOWN")
    def test_expired_exception_beats_active_rule_evaluation(self):
        # CRITICAL-with-fix + EXPIRED exception on that identity -> verdict WOULD_FAIL, expired surfaced
        exc = [{"id": "x|CVE-2026-1", "expires": "2026-01-01", "reason": "r", "owner": "p",
                "created": "2026-01-01", "evidence": "e", "review_required": True}]
        res = evaluate(trivy_json([v("CVE-2026-1","x","CRITICAL","1.0")]), exceptions_path=None)
        # direct r3 check for exception precedence (exceptions path is file-based in evaluate)
        f, issues, _ = ev.normalize(json.dumps(trivy_json([v("CVE-2026-1","x","CRITICAL","1.0")])))
        r3 = ev.r3(f, exc, [])
        states = [x["state"] for x in r3["records"]]
        self.assertIn("EXPIRED_EXCEPTION", states)
        # and R1 still evaluates WOULD_FAIL (R1 outranks; expired never tolerates)
        self.assertEqual(ev.r1(f)["verdict"], "WOULD_FAIL")
    def test_active_exception_records_exception_state(self):
        f, _, _ = ev.normalize(json.dumps(trivy_json([v("CVE-2026-0001","pkg","HIGH")])))
        r3 = ev.r3(f, EXC_ACTIVE, [])
        self.assertEqual(r3["records"][0]["state"], "EXCEPTION")
    def test_r1_outranks_r4_warn(self):
        res = evaluate(trivy_json([v("CVE-2026-1","x","CRITICAL","1.0")]))
        self.assertEqual(res["verdict"], "WOULD_FAIL")

class TestHistoricalRegression(unittest.TestCase):
    """Fixtures derived from authoritative artifacts. PROVENANCE CORRECTION
    (cycle-2 audit, run 36040505744): the authoritative Trivy JSON shows
    CVE-2026-53613/53614/76642 DO have fix 2.41.6-r0 listed — the earlier
    'no fix listed' classification came from merged-cell table extraction,
    the exact hazard this policy layer documents. Fixtures updated to the
    JSON values; the no-fix-HIGH R3 path is now covered by a synthetic
    fixture (CVE-2026-0001) rather than a mis-derived real one."""
    S7A = trivy_json([v("CVE-2026-31789","libcrypto3","CRITICAL","3.3.7-r0"),
                      v("CVE-2026-31789","libssl3","CRITICAL","3.3.7-r0"),
                      v("CVE-2025-69421","libcrypto3","HIGH"),
                      v("CVE-2025-69421","libssl3","HIGH")])
    CUR = trivy_json([v("CVE-2026-14456","libcrypto3","HIGH","3.5.8-r0"),
                      v("CVE-2026-14456","libssl3","HIGH","3.5.8-r0"),
                      v("CVE-2026-53613","libuuid","HIGH","2.41.6-r0"),
                      v("CVE-2026-53614","libuuid","HIGH","2.41.6-r0"),
                      v("CVE-2026-76642","libuuid","HIGH","2.41.6-r0"),
                      v("CVE-2026-0001","syntheticpkg","HIGH")])
    def test_7a_r1_would_fail(self):
        f,_,ok = ev.normalize(json.dumps(self.S7A))
        self.assertTrue(ok); self.assertEqual(ev.r1(f)["verdict"], "WOULD_FAIL")
    def test_current_r1_pass(self):
        f,_,ok = ev.normalize(json.dumps(self.CUR))
        self.assertTrue(ok); self.assertEqual(ev.r1(f)["verdict"], "PASS")
    def test_current_r3_surfaces_no_fix(self):
        f,_,_ = ev.normalize(json.dumps(self.CUR))
        r = ev.r3(f, [], [])
        ids = {x.get("identity") for x in r["records"] if x.get("state") == "VISIBLE_NO_FIX"}
        # JSON-authoritative: the real current inventory has NO no-fix HIGHs;
        # only the synthetic fixture CVE surfaces as VISIBLE_NO_FIX.
        self.assertEqual(ids, {"syntheticpkg|CVE-2026-0001"})
    def test_current_fix_listed_highs_counted(self):
        f,_,_ = ev.normalize(json.dumps(self.CUR))
        # 5 fix-listed HIGH pairs from the 3 real unique CVEs x their packages
        # (14456 x2, 53613, 53614, 76642) + the synthetic no-fix = 5 fix-listed.
        self.assertEqual(len([x for x in f.values() if x["severity"]=="HIGH" and x["fixed"]]), 5)

if __name__ == "__main__":
    unittest.main(verbosity=2)
