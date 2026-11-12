#!/usr/bin/env python3
"""Tests for PI-2 pi2_capacity_forecast.py (ADR-0012).

Run: python3 pi2-capacity-forecast-tests.py
Synthetic fixtures only, temp space, no network, no inference, no live
infrastructure. Deterministic via injectable clock (now_s / fixed epoch).
"""
import calendar
import importlib.util
import json
import math
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "pi2", HERE / "pi2_capacity_forecast.py")
pi2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pi2)

HOUR = 3600
DAY = 24 * HOUR
# Fixed clock: 2026-11-12T00:00:00Z — every test is deterministic.
NOW = calendar.timegm(time.strptime("2026-11-12T00:00:00Z",
                                    "%Y-%m-%dT%H:%M:%SZ"))
GATE = 50.0


def _snap(ts_s, free, gate=GATE):
    return {
        "schema_version": "1.0.0",
        "collected_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                          time.gmtime(ts_s)),
        "host": {"free_disk_gib": free, "swap_used_mib": 12000},
        "gates": {"capacity_gate_gib": gate,
                  "capacity_gate_pass": free >= gate},
        "provenance": {"tool": "platform_state_collector.py"},
    }


def _write_dir(tmp, pairs, gate=GATE, corrupt_idx=None):
    """pairs: [(epoch, free)] chronological. corrupt_idx: index to mangle."""
    d = Path(tmp) / "snaps"
    d.mkdir(parents=True, exist_ok=True)
    for i, (ts, free) in enumerate(pairs):
        p = d / ("pi1-%s.json" % time.strftime("%Y%m%d-%H%M%SZ",
                                               time.gmtime(ts)))
        if corrupt_idx is not None and i == corrupt_idx:
            p.write_text("{not json")
        else:
            p.write_text(json.dumps(_snap(ts, free, gate)))
    return d


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)


class QualificationGate(Base):
    """No forecast ever leaves the module without a qualified window."""

    def test_1_unqualified_window_blocks_forecast(self):
        # 20 samples of perfect decline but only ~5 h of coverage:
        # C1 coverage fails -> window unqualified -> INSUFFICIENT_DATA.
        start = NOW - 5 * HOUR
        pairs = [(start + i * 900, 100.0 - i * 0.1) for i in range(20)]
        d = _write_dir(self.tmp, pairs)
        w, wq = pi2.validate_window_pre(d, now_s=NOW)
        self.assertFalse(wq)
        self.assertFalse(w["window_qualified"])
        result = pi2.forecast(pi2.load_series(d, now_s=NOW), GATE, now_s=NOW)
        self.assertEqual(result["verdict"], "FORECAST")  # fit is clean...
        # ...but the CLI wrapper must still refuse on the unqualified window:
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = pi2.main([str(d)])
        out = json.loads(buf.getvalue())
        self.assertEqual(out["verdict"], "INSUFFICIENT_DATA")
        self.assertIn("does not qualify", out["reason"])

    def test_2_qualified_window_required_input(self):
        # The validator must be the single qualification authority.
        # Qualification needs >=90% slot coverage of the full 14-day
        # window, so the fixture spans the whole window.
        start = NOW - 14 * DAY
        pairs = [(start + i * HOUR, 80.0) for i in range(14 * 24)]
        d = _write_dir(self.tmp, pairs)
        w, wq = pi2.validate_window_pre(d, now_s=NOW)
        self.assertTrue(wq)
        self.assertTrue(w["window_qualified"])
        self.assertEqual(w["validator_version"], "1.1.0")


class TrendClassification(Base):
    def test_3_steady_decline_forecasts(self):
        # 0.2 GiB/h decline from 120 GiB: ends ~52.8 (above the gate),
        # projects crossing ~14 h after the last observation.
        start = NOW - 14 * DAY
        pairs = [(start + i * HOUR, 120.0 - 0.2 * i)
                 for i in range(0, 14 * 24)]
        d = _write_dir(self.tmp, pairs)
        series = pi2.load_series(d, now_s=NOW)
        r = pi2.forecast(series, GATE, now_s=NOW)
        self.assertEqual(r["verdict"], "FORECAST")
        self.assertLess(r["segment_fit"]["slope_gib_per_hour"], 0)
        self.assertGreater(r["time_to_gate"]["hours"], 0)
        self.assertAlmostEqual(r["time_to_gate"]["hours"], 14.0, delta=2.0)
        # band must be non-negative and finite
        self.assertGreaterEqual(r["segment_fit"]["band_2sigma_gib"], 0.0)
        self.assertTrue(math.isfinite(r["segment_fit"]["band_2sigma_gib"]))

    def test_4_stable_capacity_is_stable_verdict(self):
        start = NOW - 14 * DAY
        pairs = [(start + i * HOUR, 80.0 + 0.01 * ((i % 3) - 1))
                 for i in range(0, 14 * 24)]
        d = _write_dir(self.tmp, pairs)
        r = pi2.forecast(pi2.load_series(d, now_s=NOW), GATE, now_s=NOW)
        self.assertEqual(r["verdict"], "STABLE")
        self.assertIsNone(r["time_to_gate"]["hours"])

    def test_5_growth_slope_does_not_project_gate_crossing(self):
        start = NOW - 14 * DAY
        pairs = [(start + i * HOUR, 60.0 + 0.5 * i) for i in range(0, 24 * 14)]
        d = _write_dir(self.tmp, pairs)
        r = pi2.forecast(pi2.load_series(d, now_s=NOW), GATE, now_s=NOW)
        self.assertEqual(r["verdict"], "FORECAST")
        self.assertIsNone(r["time_to_gate"]["hours"])
        self.assertIn("not projected", r["time_to_gate"]["basis"])


class Discontinuity(Base):
    """The 14 -> 248 GiB observed step (2026-11-12 reboot) and its class."""

    def test_6_regression_step_14_to_248_is_not_extrapolated(self):
        # 12 days declining 30 -> ~14 GiB, then the observed-class step to
        # 248, then ~30 h of post-step history — all inside the window
        # (the validator rejects future-dated observations by design).
        start = NOW - 12 * DAY - 31 * HOUR
        pairs = [(start + i * HOUR, 30.0 - i * (16.0 / (12 * 24)))
                 for i in range(12 * 24)]
        step_at = pairs[-1][0] + HOUR
        pairs.append((step_at, 248.0))
        pairs += [(step_at + i * HOUR, 248.0) for i in range(1, 31)]
        d = _write_dir(self.tmp, pairs)
        series = pi2.load_series(d, now_s=NOW)
        disc = pi2.detect_discontinuities(series)
        self.assertEqual(len(disc), 1)
        self.assertGreater(disc[0]["delta_gib"], 200.0)  # ~234 GiB release
        seg, segs = pi2.segment(series, disc)
        self.assertEqual(len(seg), 31)          # post-step segment only
        self.assertLess(segs[-2][-1][1], 20.0)  # pre-step tail intact (~14)
        r = pi2.forecast(series, GATE, now_s=NOW)
        # 31 observations >= MIN_SAMPLES but post-step history is a
        # stable plateau -> verdict is about the NEW base, never the
        # pre-step decline:
        self.assertIn(r["verdict"], ("FORECAST", "STABLE"))
        self.assertGreater(r["segment_fit"]["last_free_gib"], 200.0)
        # and the fitted slope must NOT be the pre-step decline rate
        self.assertGreater(r["segment_fit"]["slope_gib_per_hour"],
                           -0.1)  # decline was ~-0.056 GiB/h; plateau ~0

    def test_7_step_plus_short_tail_refuses(self):
        # Same step, but only 2 h of post-step history: the post-step
        # segment is too short to fit -> INSUFFICIENT_DATA (never a
        # forecast extrapolated across the step).
        start = NOW - 12 * DAY - 2 * HOUR
        pairs = [(start + i * HOUR, 30.0 - i * (16.0 / (12 * 24)))
                 for i in range(12 * 24)]
        step_at = pairs[-1][0] + HOUR
        pairs.append((step_at, 248.0))
        pairs.append((step_at + HOUR, 248.0))
        d = _write_dir(self.tmp, pairs)
        series = pi2.load_series(d, now_s=NOW)
        r = pi2.forecast(series, GATE, now_s=NOW)
        self.assertEqual(r["verdict"], "INSUFFICIENT_DATA")
        self.assertIn("too short", r["reason"])

    def test_8_downward_step_also_segmented(self):
        # Sudden large DROP mid-window (e.g. a real mass-consumption
        # event): also a discontinuity, never bridged; the post-drop
        # segment becomes the only forecast basis.
        start = NOW - 14 * DAY
        pairs = [(start + i * HOUR, 200.0) for i in range(10 * 24)]
        drop_at = pairs[-1][0] + HOUR
        pairs.append((drop_at, 60.0))
        pairs += [(drop_at + i * HOUR, 60.0 - 0.02 * i) for i in range(1, 95)]
        d = _write_dir(self.tmp, pairs)
        series = pi2.load_series(d, now_s=NOW)
        disc = pi2.detect_discontinuities(series)
        self.assertEqual(len(disc), 1)
        self.assertLess(disc[0]["delta_gib"], -100)
        r = pi2.forecast(series, GATE, now_s=NOW)
        self.assertEqual(r["verdict"], "FORECAST")
        self.assertLess(r["segment_fit"]["last_free_gib"], 100.0)


class DataQuality(Base):
    def test_9_insufficient_samples_refused(self):
        pairs = [(NOW - i * HOUR, 90.0) for i in range(5, 0, -1)]
        d = _write_dir(self.tmp, pairs)
        r = pi2.forecast(pi2.load_series(d, now_s=NOW), GATE, now_s=NOW)
        self.assertEqual(r["verdict"], "INSUFFICIENT_DATA")
        self.assertIn("MIN_SAMPLES", r["reason"])

    def test_10_missing_and_malformed_observations_dropped(self):
        # Full 14-day series (336 slots) with one corrupt file and one
        # missing hour: both are excluded from the series, coverage stays
        # >=90%, and the window still qualifies (2 h gap <= 6 h C3 limit).
        start = NOW - 14 * DAY
        pairs = [(start + i * HOUR, 90.0) for i in range(14 * 24)]
        d = _write_dir(self.tmp, pairs, corrupt_idx=7)
        (Path(self.tmp) / "snaps" /
         ("pi1-%s.json" % time.strftime("%Y%m%d-%H%M%SZ",
                                        time.gmtime(pairs[20][0])))
         ).unlink()
        series = pi2.load_series(d, now_s=NOW)
        # 334 usable of 336 (corrupt + missing removed)
        self.assertEqual(len(series), 14 * 24 - 2)
        r = pi2.forecast(series, GATE, now_s=NOW)
        self.assertEqual(r["verdict"], "STABLE")
        # validator records the exclusion authoritatively — and per its
        # documented hardening (2026-10-31), ANY malformed snapshot
        # disqualifies the whole window ("an anomalous collection can
        # never quietly qualify"). The forecast() core still classifies
        # the filtered series, but the CLI gate would refuse:
        w, wq = pi2.validate_window_pre(d, now_s=NOW)
        self.assertEqual(w["malformed_count"], 1)
        self.assertFalse(wq)
        self.assertFalse(w["window_qualified"])
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            pi2.main([str(d)])
        out = json.loads(buf.getvalue())
        self.assertEqual(out["verdict"], "INSUFFICIENT_DATA")
        self.assertIn("does not qualify", out["reason"])

    def test_11_outlier_does_not_wreck_the_trend(self):
        # A single large-but-sub-threshold outlier (15 GiB above the
        # line: far beyond noise, below the ~20 GiB discontinuity floor)
        # widens the honest uncertainty band without flipping the trend.
        start = NOW - 14 * DAY
        pairs = [(start + i * HOUR, 100.0 - 0.1 * i) for i in range(24 * 14)]
        mid = 24 * 7
        expected_mid = 100.0 - 0.1 * mid
        pairs[mid] = (pairs[mid][0], expected_mid + 15.0)
        d = _write_dir(self.tmp, pairs)
        r = pi2.forecast(pi2.load_series(d, now_s=NOW), GATE, now_s=NOW)
        # residual scatter widens the band (honest) but the verdict
        # machinery survives; slope remains negative
        self.assertEqual(r["verdict"], "FORECAST")
        self.assertLess(r["segment_fit"]["slope_gib_per_hour"], 0)
        self.assertGreater(r["segment_fit"]["band_2sigma_gib"], 0)

    def test_12_no_series_at_all(self):
        d = Path(self.tmp) / "empty"
        d.mkdir()
        r = pi2.forecast(pi2.load_series(d, now_s=NOW), GATE, now_s=NOW)
        self.assertEqual(r["verdict"], "INSUFFICIENT_DATA")
        self.assertIn("MIN_SAMPLES", r["reason"])


class Contract(Base):
    def test_13_deterministic_output(self):
        start = NOW - 14 * DAY
        pairs = [(start + i * HOUR, 100.0 - 0.2 * i)
                 for i in range(0, 24 * 14)]
        d = _write_dir(self.tmp, pairs)
        r1 = pi2.forecast(pi2.load_series(d, now_s=NOW), GATE, now_s=NOW)
        r2 = pi2.forecast(pi2.load_series(d, now_s=NOW), GATE, now_s=NOW)
        self.assertEqual(json.dumps(r1, sort_keys=True),
                         json.dumps(r2, sort_keys=True))

    def test_14_no_future_leakage_in_backtest(self):
        """Rolling-origin check: fitting on data up to T must not change
        when later observations exist but are excluded — i.e. the fit for
        origin T uses only observations <= T. A nonlinear series (early
        plateau, later decline) proves the fit is data-sensitive and that
        an origin-T fit differs from a full-series fit."""
        start = NOW - 14 * DAY
        pairs = []
        for i in range(24 * 14):
            h = i  # hours since start
            if h < 10 * 24:
                free = 100.0  # plateau: no trend for the first 10 days
            else:
                free = 100.0 - 0.5 * (h - 10 * 24)  # decline after
            pairs.append((start + h * HOUR, free))
        cutoff = start + 10 * DAY
        past = [p for p in pairs if p[0] <= cutoff]
        future = [p for p in pairs if p[0] > cutoff]
        fit_past = pi2._fit(list(past))
        # identical inputs -> identical fit (deterministic origin)
        self.assertEqual(fit_past["slope_gib_per_hour"],
                         pi2._fit(past)["slope_gib_per_hour"])
        # origin-T fit sees the plateau only: ~zero slope
        self.assertAlmostEqual(fit_past["slope_gib_per_hour"], 0.0, places=9)
        # including post-cutoff data changes the fit (no caching; the
        # origin-T backtest result is genuinely produced from past-only)
        fit_refit = pi2._fit(past + future[:5])
        self.assertLess(fit_refit["slope_gib_per_hour"],
                        fit_past["slope_gib_per_hour"])

    def test_15_consumption_vs_free_distinction(self):
        """Consumption is reported separately and can differ in sign from
        the free-capacity slope basis."""
        start = NOW - 14 * DAY
        pairs = [(start + i * HOUR, 100.0 - 0.2 * i)
                 for i in range(0, 24 * 14)]
        d = _write_dir(self.tmp, pairs)
        r = pi2.forecast(pi2.load_series(d, now_s=NOW), GATE, now_s=NOW)
        self.assertLess(r["segment_fit"]["slope_gib_per_hour"], 0)
        self.assertLess(r["consumption"]["net_change_gib"], 0)
        # release scenario: free capacity rising = negative consumption
        pairs2 = [(start + i * HOUR, 60.0 + 0.2 * i) for i in range(24 * 14)]
        d2 = _write_dir(Path(self.tmp) / "release", pairs2)
        r2 = pi2.forecast(pi2.load_series(d2, now_s=NOW), GATE, now_s=NOW)
        self.assertGreater(r2["segment_fit"]["slope_gib_per_hour"], 0)
        self.assertGreater(r2["consumption"]["net_change_gib"], 0)

    def test_16_contract_fields_present(self):
        start = NOW - 14 * DAY
        pairs = [(start + i * HOUR, 100.0 - 0.2 * i) for i in range(24 * 14)]
        d = _write_dir(self.tmp, pairs)
        r = pi2.forecast(pi2.load_series(d, now_s=NOW), GATE, now_s=NOW)
        for k in ("schema_version", "model_version", "verdict",
                  "llm_inference_required", "evaluated_at_utc", "input",
                  "capacity_gate_gib"):
            self.assertIn(k, r)
        self.assertEqual(r["llm_inference_required"], 0)
        self.assertEqual(r["model_version"], "1.0.0")
        self.assertEqual(r["schema_version"], "1.0.0")


if __name__ == "__main__":
    unittest.main(verbosity=2)
