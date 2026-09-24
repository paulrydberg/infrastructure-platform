#!/usr/bin/env python3
"""Unit + historical-regression tests for the Phase 7C shadow evaluator.
Deterministic, stdlib-only, no network. Run: python3 tools/policy/test_shadow_evaluator.py
Exit 0 = all pass."""
import json, os, sys, tempfile, datetime, unittest

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

class TestR1(unittest.TestCase):
    def test_critical_with_fix_would_fail(self):
        r = ev.r1(ev.normalize(json.dumps(trivy_json([v("CVE-2026-31789","libssl3","CRITICAL","3.3.7-r0")])))[0])
        self.assertEqual(r["verdict"], "WOULD_FAIL")
    def test_critical_no_fix_not_silent(self):
        r = ev.r1(ev.normalize(json.dumps(trivy_json([v("CVE-2026-99999","x","CRITICAL")])))[0])
        self.assertEqual(r["verdict"], "PASS")  # R1 doesn't fail...
        self.assertEqual(len(r["critical_no_fix"]), 1)  # ...but R3 must surface it

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
        cur = trivy_json([v("CVE-2026-1","a","HIGH")])  # fix dropped
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
    def test_malformed_current_never_passes_silently(self):
        res = ev.evaluate.__wrapped__ if hasattr(ev.evaluate, "__wrapped__") else None
        p = os.path.join(TMP, "bad.json"); open(p, "w").write("{not json")
        out = ev.evaluate(p, None, render("r.yaml", RENDERED_OK), None, "test", "t")
        self.assertEqual(out["verdict"], "UNKNOWN")

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
        f,_ = ev.normalize(json.dumps(self.S7A))
        self.assertEqual(ev.r1(f)["verdict"], "WOULD_FAIL")
    def test_current_r1_pass(self):
        f,_ = ev.normalize(json.dumps(self.CUR))
        self.assertEqual(ev.r1(f)["verdict"], "PASS")
    def test_current_r3_surfaces_no_fix(self):
        f,_ = ev.normalize(json.dumps(self.CUR))
        r = ev.r3(f, [], [])
        ids = {x.get("identity") for x in r["records"] if x.get("state") == "VISIBLE_NO_FIX"}
        # JSON-authoritative: the real current inventory has NO no-fix HIGHs;
        # only the synthetic fixture CVE surfaces as VISIBLE_NO_FIX.
        self.assertEqual(ids, {"syntheticpkg|CVE-2026-0001"})
    def test_current_fix_listed_highs_counted(self):
        f,_ = ev.normalize(json.dumps(self.CUR))
        # 5 fix-listed HIGH pairs from the 3 real unique CVEs x their packages
        # (14456 x2, 53613, 53614, 76642) + the synthetic no-fix = 5 fix-listed.
        self.assertEqual(len([x for x in f.values() if x["severity"]=="HIGH" and x["fixed"]]), 5)

if __name__ == "__main__":
    unittest.main(verbosity=2)
