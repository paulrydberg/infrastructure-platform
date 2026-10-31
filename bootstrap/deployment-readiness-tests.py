#!/usr/bin/env python3
"""Tests for PI-3 deployment_readiness_evaluator.py (ADR-0012).

Run: python3 deployment-readiness-tests.py
"""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "deployment_readiness_evaluator", HERE / "deployment_readiness_evaluator.py")
dre = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dre)


def _snap(free=26, pods=None, k3s_rss="1.11GiB / 1.5GiB", swap=11102):
    if pods is None:
        pods = {
            "argocd/argocd-server": {"ready": "1/1", "status": "Running", "restarts": "65"},
            "kube-system/coredns": {"ready": "1/1", "status": "Running", "restarts": "64"},
            "platform-demo/platform-demo": {"ready": "1/1", "status": "Running", "restarts": "81"},
        }
    return {
        "collected_at_utc": "2026-10-30T19:00:00Z",
        "host": {"free_disk_gib": free, "swap_used_mib": swap},
        "docker": {"k3s_server_mem_usage": k3s_rss},
        "k3s": {"pods": pods, "pod_count": len(pods)},
        "gates": {"capacity_gate_gib": 50, "capacity_gate_pass": free >= 50},
    }


class TestThresholdContract(unittest.TestCase):
    """The evaluator mirrors DOCUMENTED gates — drift here must fail tests."""

    def test_01_capacity_threshold_is_documented_50gib(self):
        self.assertEqual(dre.THRESHOLDS["capacity_gate_gib"], 50)

    def test_02_k3s_cap_is_documented_1p5(self):
        self.assertEqual(dre.THRESHOLDS["k3s_cap_gib"], 1.5)

    def test_03_mem_free_pct_is_documented_35(self):
        self.assertEqual(dre.THRESHOLDS["mem_free_pct_min"], 35)


class TestVerdicts(unittest.TestCase):
    def test_10_capacity_fail_is_blocking_not_ready(self):
        v = dre.evaluate(_snap(free=26))
        self.assertEqual(v["verdict"], "NOT_READY")
        self.assertIn("capacity_gate", v["blocking"])

    def test_11_capacity_pass_with_healthy_pods_is_ready(self):
        v = dre.evaluate(_snap(free=57))
        self.assertEqual(v["verdict"], "READY")
        self.assertEqual(v["blocking"], [])

    def test_12_exact_50gib_passes(self):
        v = dre.evaluate(_snap(free=50))
        by = {c["criterion"]: c["verdict"] for c in v["criteria"]}
        self.assertEqual(by["capacity_gate"], "PASS")

    def test_13_missing_disk_is_insufficient_data_never_ready(self):
        """UNKNOWN criteria must never produce READY — fail closed."""
        s = _snap(free=57)
        s["host"]["free_disk_gib"] = None
        v = dre.evaluate(s)
        self.assertEqual(v["verdict"], "INSUFFICIENT_DATA")
        self.assertIn("capacity_gate", v["unknown"])

    def test_14_unhealthy_pod_is_blocking(self):
        pods = {
            "argocd/argocd-server": {"ready": "0/1", "status": "Running", "restarts": "9"},
            "kube-system/coredns": {"ready": "1/1", "status": "Running", "restarts": "6"},
        }
        v = dre.evaluate(_snap(free=57, pods=pods))
        self.assertEqual(v["verdict"], "NOT_READY")
        self.assertIn("k3s_pods_healthy", v["blocking"])

    def test_15_crashloop_pod_is_blocking(self):
        pods = {
            "x/y": {"ready": "0/1", "status": "CrashLoopBackOff", "restarts": "12"},
        }
        v = dre.evaluate(_snap(free=57, pods=pods))
        self.assertEqual(v["verdict"], "NOT_READY")

    def test_16_k3s_over_cap_is_fail(self):
        v = dre.evaluate(_snap(free=57, k3s_rss="1.51GiB / 1.5GiB"))
        by = {c["criterion"]: c["verdict"] for c in v["criteria"]}
        self.assertEqual(by["k3s_memory_envelope"], "FAIL")
        self.assertEqual(v["verdict"], "NOT_READY")

    def test_17_k3s_in_warn_band_is_warn_not_fail(self):
        v = dre.evaluate(_snap(free=57, k3s_rss="1.40GiB / 1.5GiB"))
        by = {c["criterion"]: c["verdict"] for c in v["criteria"]}
        self.assertEqual(by["k3s_memory_envelope"], "WARN")
        self.assertEqual(v["verdict"], "READY")  # WARN does not block

    def test_18_swap_residency_is_info_never_blocking(self):
        """resource-gate-principles.md: residency != pressure. 11 GiB residency
        must NOT block the verdict."""
        v = dre.evaluate(_snap(free=57, swap=11102))
        by = {c["criterion"]: c["verdict"] for c in v["criteria"]}
        self.assertEqual(by["swap_residency_informational"], "INFO")
        self.assertEqual(v["verdict"], "READY")

    def test_19_missing_pods_block_is_insufficient(self):
        s = _snap(free=57)
        s["k3s"]["pods"] = None
        v = dre.evaluate(s)
        self.assertEqual(v["verdict"], "INSUFFICIENT_DATA")

    def test_20_missing_snapshot_keys_insufficient(self):
        v = dre.evaluate({"host": {}})
        self.assertEqual(v["verdict"], "INSUFFICIENT_DATA")


class TestContract(unittest.TestCase):
    def test_30_zero_inference(self):
        v = dre.evaluate(_snap())
        self.assertEqual(v["llm_inference_required"], 0)

    def test_31_provenance_present(self):
        v = dre.evaluate(_snap())
        self.assertEqual(v["evaluator_version"], "1.0.0")
        self.assertTrue(v["snapshot_collected_at_utc"])

    def test_32_criterion_sources_cite_evidence_docs(self):
        v = dre.evaluate(_snap())
        for c in v["criteria"]:
            self.assertTrue(c.get("source"), f"criterion {c['criterion']} lacks source")


class TestCli(unittest.TestCase):
    def test_40_cli_roundtrip(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(_snap(free=57), f)
            snap_path = f.name
        out_path = snap_path + ".verdict"
        rc = dre.main([snap_path, "-o", out_path])
        self.assertEqual(rc, 0)
        v = json.loads(Path(out_path).read_text())
        self.assertEqual(v["verdict"], "READY")

    def test_41_cli_missing_file_errors(self):
        self.assertEqual(dre.main(["/nonexistent/snap.json"]), 2)

    def test_42_cli_invalid_json_errors(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write("{not json")
            p = f.name
        self.assertEqual(dre.main([p]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
