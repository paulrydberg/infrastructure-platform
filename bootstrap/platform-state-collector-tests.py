#!/usr/bin/env python3
"""Tests for PI-1 platform_state_collector.py (ADR-0012).

Run: python3 platform-state-collector-tests.py
"""
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "platform_state_collector", HERE / "platform_state_collector.py")
psc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(psc)


class TestValidation(unittest.TestCase):
    def test_01_valid_minimal_snapshot_passes(self):
        snap = {
            "schema_version": psc.SCHEMA_VERSION,
            "collector_version": psc.COLLECTOR_VERSION,
            "collected_at_utc": "2026-10-30T00:00:00Z",
            "provenance": {"probe_errors": [], "llm_inference_required": 0},
            "host": {"free_disk_gib": 26, "swap_used_mib": 11102},
            "docker": {},
            "k3s": {},
            "gates": {},
        }
        self.assertEqual(psc.validate_snapshot(snap), [])

    def test_02_missing_required_keys_rejected(self):
        errs = psc.validate_snapshot({"schema_version": "x"})
        self.assertTrue(any("missing keys" in e for e in errs))

    def test_03_wrong_schema_version_rejected(self):
        snap = {"schema_version": "0.9.0", "collector_version": "1.0.0",
                "collected_at_utc": "t", "provenance": {"probe_errors": [],
                "llm_inference_required": 0}, "host": {}}
        errs = psc.validate_snapshot(snap)
        self.assertTrue(any("schema_version" in e for e in errs))

    def test_04_null_probe_data_is_legal(self):
        """Missing probe data must be null, not fabricated — validation accepts null."""
        snap = {"schema_version": psc.SCHEMA_VERSION,
                "collector_version": psc.COLLECTOR_VERSION,
                "collected_at_utc": "t",
                "provenance": {"probe_errors": ["df failed"],
                               "llm_inference_required": 0},
                "host": {"free_disk_gib": None, "swap_used_mib": None},
                "docker": {}, "k3s": {}, "gates": {}}
        self.assertEqual(psc.validate_snapshot(snap), [])

    def test_05_negative_disk_rejected(self):
        snap = {"schema_version": psc.SCHEMA_VERSION,
                "collector_version": psc.COLLECTOR_VERSION,
                "collected_at_utc": "t",
                "provenance": {"probe_errors": [], "llm_inference_required": 0},
                "host": {"free_disk_gib": -1, "swap_used_mib": None},
                "docker": {}, "k3s": {}, "gates": {}}
        errs = psc.validate_snapshot(snap)
        self.assertTrue(any("non-negative" in e for e in errs))

    def test_06_absence_of_provenance_errors_rejected(self):
        """Silence about probe failures is not allowed — probe_errors required."""
        snap = {"schema_version": psc.SCHEMA_VERSION,
                "collector_version": psc.COLLECTOR_VERSION,
                "collected_at_utc": "t", "provenance": {},
                "host": {"free_disk_gib": None, "swap_used_mib": None},
                "docker": {}, "k3s": {}, "gates": {}}
        errs = psc.validate_snapshot(snap)
        self.assertTrue(any("probe_errors" in e for e in errs))


class TestParsing(unittest.TestCase):
    def test_10_df_g_parse_known_format(self):
        fake = "Filesystem 1G-blocks Used Available Capacity iused\n" \
               "/dev/disk2s4s1 698 10 26 29% 426864 294307160 0% /\n"
        with mock.patch.object(psc, "_run", return_value=(0, fake)):
            self.assertEqual(psc._parse_df_g_root(), 26)

    def test_11_df_g_failure_returns_none(self):
        with mock.patch.object(psc, "_run", return_value=(1, "")):
            self.assertIsNone(psc._parse_df_g_root())

    def test_12_swap_parse(self):
        fake = "vm.swapusage: total = 12288.00M  used = 11102.00M  free = 1186.00M"
        with mock.patch.object(psc, "_run", return_value=(0, fake)):
            used, total = psc._parse_swap()
            self.assertEqual((used, total), (11102, 12288))

    def test_12b_swap_parse_with_comma_thousands(self):
        fake = "vm.swapusage: total = 12,288.00M  used = 11,102.00M  free = 1,186.00M"
        with mock.patch.object(psc, "_run", return_value=(0, fake)):
            used, total = psc._parse_swap()
            self.assertEqual((used, total), (11102, 12288))

    def test_13_swap_parse_failure(self):
        with mock.patch.object(psc, "_run", return_value=(1, "")):
            self.assertEqual(psc._parse_swap(), (None, None))


class TestGateSemantics(unittest.TestCase):
    """The collector REPORTS against documented gates — never redefines them."""

    def test_20_gate_threshold_is_documented_value(self):
        snap = psc.collect.__wrapped__() if hasattr(psc.collect, "__wrapped__") else None
        # threshold comes from the documented 50 GiB deployment gate
        snap = psc.collect()
        self.assertEqual(snap["gates"]["capacity_gate_gib"], 50)
        self.assertEqual(snap["gates"]["k3s_cap_gib"], 1.5)

    def test_21_gate_pass_reflects_free_disk(self):
        with mock.patch.object(psc, "_parse_df_g_root", return_value=13), \
             mock.patch.object(psc, "_parse_swap", return_value=(11102, 12288)), \
             mock.patch.object(psc, "_parse_docker_df", return_value=None), \
             mock.patch.object(psc, "_parse_docker_stats", return_value=None), \
             mock.patch.object(psc, "_parse_k3s_pods", return_value=None):
            snap = psc.collect()
        self.assertIs(snap["gates"]["capacity_gate_pass"], False)

    def test_22_probe_failure_leaves_gate_unknown_not_pass(self):
        """df failure -> gate unknown (null). NEVER a fabricated PASS."""
        with mock.patch.object(psc, "_parse_df_g_root", return_value=None), \
             mock.patch.object(psc, "_parse_swap", return_value=(1, 2)), \
             mock.patch.object(psc, "_parse_docker_df", return_value=None), \
             mock.patch.object(psc, "_parse_docker_stats", return_value=None), \
             mock.patch.object(psc, "_parse_k3s_pods", return_value=None):
            snap = psc.collect()
        self.assertIsNone(snap["gates"]["capacity_gate_pass"])
        self.assertTrue(snap["provenance"]["probe_errors"])

    def test_23_zero_inference_contract(self):
        snap = psc.collect()
        self.assertEqual(snap["provenance"]["llm_inference_required"], 0)


class TestLiveE2E(unittest.TestCase):
    """E2E against the real host (read-only). Probes may legitimately fail
    (e.g. docker down) — the contract under test is honest nulls + valid
    structure, not specific values."""

    def test_30_live_collection_is_structurally_valid(self):
        snap = psc.collect()
        self.assertEqual(psc.validate_snapshot(snap), [],
                         f"validation errors: {psc.validate_snapshot(snap)}")

    def test_31_live_main_emits_and_exits_zero(self):
        rc = psc.main([])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
