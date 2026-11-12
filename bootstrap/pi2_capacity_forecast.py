#!/usr/bin/env python3
"""PI-2 — deterministic capacity-forecast model over PI-1 snapshot history.

ADR-0012 (ACCEPTED 2026-10-31) mandates the platform-intelligence layer as
deterministic collectors/evaluators: stdlib-only, zero LLM/runtime inference,
no silent fallbacks, honest failure classification. This module is the PI-2
forecast model. Its unlock prerequisite — a PI-1 evidence window that PASSES
bootstrap/evidence_window_validator.py — is machine-checked here on every
invocation (imported, never copied, so the two cannot drift).

What it forecasts
-----------------
A linear trend of host free-disk capacity (GiB) over the qualified window,
with a confidence band derived from residual scatter, an estimated time to
the capacity gate, and an explicit, conservative verdict vocabulary.

What it refuses to do
---------------------
- Extrapolate across a capacity DISCONTINUITY. A step change (e.g. the
  measured 14 -> 248 GiB release on 2026-11-12, or purgeable-space release)
  is a change in the measured base, not a trend. Forecasting across one
  would present a pinned/purged-space artifact as future capacity.
- Fabricate precision. Fewer than MIN_SAMPLES usable observations, or a
  post-discontinuity tail too short to fit, yields INSUFFICIENT_DATA.
- Conflate free capacity with consumption. Free space is an unsigned
  quantity bounded by volume size; consumption = free_at_end - free_at_start
  over the segment (negative = net consumption, positive = net release).
  The trend is fit on free capacity; the consumption rate is reported
  separately as an interpretive value, never as the forecast basis.

Verdict vocabulary (mirrors PI-3/PI-6 conventions)
--------------------------------------------------
- FORECAST       : a segment-fit exists, meets MIN_SAMPLES, residuals allow
                   a band; output includes projected slope, band, time-to-gate.
- STABLE         : slope is not meaningfully different from zero relative to
                   residual noise (|slope| < 2 * slope_stderr) — no trend to
                   forecast; this is a healthy, honest result, not a failure.
- INSUFFICIENT_DATA : below MIN_SAMPLES, window not qualified, or no
                   sufficiently long post-discontinuity segment. Refusal is
                   explicit and carries the reason; never upgraded by
                   elapsed time.

Determinism: same snapshot dir + same injected clock -> byte-identical
output modulo nothing (generated_at comes only from the injectable clock;
when now_s is None the wall clock is used, matching PI-1/PI-3 conventions).
No network, no inference, no writes (stdout or explicit --out only).
"""
import argparse
import calendar
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import evidence_window_validator as evw  # noqa: E402 (single authority)

MODEL_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
LLM_INFERENCE_REQUIRED = 0

# Explicit minimum-sample requirement (mandate): below this, no fit.
MIN_SAMPLES = 8
# Discontinuity detection: a log10(|delta|) jump is material when the
# one-hour change exceeds JUMP_LOG10_GIB decades of GiB (10^1.3 ~ 20 GiB
# in one hour — beyond any plausible real consumption/reclamation rate
# and matching the observed purgeable/pinned release mechanism).
JUMP_LOG10_GIB = 1.3
# A segment shorter than this (in hours of span) is never fit after a
# discontinuity — reported INSUFFICIENT_DATA instead.
MIN_SEGMENT_HOURS = 24.0
# Validation window length must match the validator's own default (14
# days — see evidence_window_validator.validate_window); single value
# defined once here and passed explicitly to both calls.
WINDOW_DAYS = 14
# Fallback gate line when the window's C4 threshold record is absent
# (single documented value: bootstrap.sh:66 deployment prerequisite).
DEFAULT_GATE_GIB = 50.0


def _parse_ts(ts):
    """Parse PI-1 collected_at_utc (ISO8601 Z) to epoch seconds. None on
    malformed input (caller treats as anomalous and drops the sample)."""
    try:
        return calendar.timegm(time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ"))
    except (TypeError, ValueError):
        return None


def _free_gib(snapshot):
    host = snapshot.get("host") or {}
    v = host.get("free_disk_gib")
    if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0:
        return float(v)
    return None


def load_series(dirpath, now_s=None):
    """Chronological [(epoch_s, free_gib)] from schema-valid snapshots in
    the trailing validator window. Malformed/duplicate/future-dated
    observations are dropped (conservatively) — the validator's counts
    remain the authoritative record of what was excluded."""
    records, _malformed = evw._load_snapshots(Path(dirpath), WINDOW_DAYS,
                                              now_s=now_s)
    series = []
    if records:
        for r in records:
            rec = r.get("record") or {}
            f = _free_gib(rec)
            if f is not None:
                series.append((r["ts"], f))
    series.sort(key=lambda p: p[0])
    return series


def detect_discontinuities(series):
    """Indices i where series[i] - series[i-1] is a material step change.
    A one-hour jump in free space of >= 10^JUMP_LOG10_GIB GiB (up or down)
    cannot be ordinary consumption and marks a change of measured base."""
    threshold = 10.0 ** JUMP_LOG10_GIB
    out = []
    for i in range(1, len(series)):
        delta = series[i][1] - series[i - 1][1]
        if abs(delta) >= threshold:
            out.append({"index": i, "at_utc": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(series[i][0])),
                "delta_gib": round(delta, 1)})
    return out


def segment(series, discontinuities):
    """Split the series at discontinuities. Returns the LAST segment (the
    only one a forecast may legitimately extrapolate) plus the full list."""
    if not series:
        return [], []
    cuts = {0} | {d["index"] for d in discontinuities}
    bounds = sorted(cuts | {len(series)})
    segments = [series[bounds[i]:bounds[i + 1]]
                for i in range(len(bounds) - 1)]
    segments = [s for s in segments if s]
    return segments[-1], segments


def _fit(points):
    """Ordinary least squares on (hours_since_start, free_gib).
    Returns dict with slope GiB/h, intercept, stderr of slope, residual
    std-dev, n. Pure arithmetic — stdlib only."""
    n = len(points)
    t0 = points[0][0]
    xs = [(p[0] - t0) / 3600.0 for p in points]
    ys = [p[1] for p in points]
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx if sxx > 0 else 0.0
    intercept = my - slope * mx
    resid = [y - (intercept + slope * x) for x, y in zip(xs, ys)]
    ssr = sum(r * r for r in resid)
    dof = max(n - 2, 1)
    resid_sd = math.sqrt(ssr / dof)
    slope_se = resid_sd / math.sqrt(sxx) if sxx > 0 else float("inf")
    return {"slope_gib_per_hour": slope, "intercept_gib": intercept,
            "slope_stderr": slope_se, "residual_sd": resid_sd,
            "n": n, "t0": t0, "span_hours": xs[-1] - xs[0]}


def forecast(series, gate_gib, now_s=None):
    """Produce the PI-2 verdict dict. Deterministic given inputs."""
    now = now_s if now_s is not None else calendar.timegm(time.gmtime())
    last_seg, all_segs = segment(series, detect_discontinuities(series))
    n_total = len(series)
    base = {
        "schema_version": SCHEMA_VERSION,
        "model_version": MODEL_VERSION,
        "llm_inference_required": LLM_INFERENCE_REQUIRED,
        "evaluated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                          time.gmtime(now)),
        "input": {"observations_total": n_total,
                  "discontinuities": detect_discontinuities(series),
                  "segments": len(all_segs),
                  "last_segment_observations": len(last_seg)},
        "capacity_gate_gib": gate_gib,
    }
    if n_total < MIN_SAMPLES:
        return {**base, "verdict": "INSUFFICIENT_DATA", "reason":
                "fewer than MIN_SAMPLES usable observations in the "
                "qualified window (%d < %d)" % (n_total, MIN_SAMPLES)}
    if len(last_seg) < MIN_SAMPLES or (len(all_segs) > 1 and
                                       last_seg[-1][0] - last_seg[0][0]
                                       < MIN_SEGMENT_HOURS * 3600):
        return {**base, "verdict": "INSUFFICIENT_DATA", "reason":
                "post-discontinuity segment too short to fit "
                "(%d observations, %.1f h span; need >=%d and >=%.0f h)"
                % (len(last_seg), (last_seg[-1][0] - last_seg[0][0]) / 3600.0
                   if last_seg else 0.0, MIN_SAMPLES, MIN_SEGMENT_HOURS)}
    fit = _fit(last_seg)
    # Honest uncertainty: a 95%-style band from residual scatter and slope
    # stderr (2-sigma, normal approximation — conservative, interpretable).
    band = 2.0 * fit["residual_sd"]
    slope_lo = fit["slope_gib_per_hour"] - 2.0 * fit["slope_stderr"]
    slope_hi = fit["slope_gib_per_hour"] + 2.0 * fit["slope_stderr"]
    stable = abs(fit["slope_gib_per_hour"]) <= 2.0 * fit["slope_stderr"]
    t_last, f_last = last_seg[-1]
    hours_to_gate = None
    if not stable and fit["slope_gib_per_hour"] < 0:
        hours_to_gate = (f_last - gate_gib) / -fit["slope_gib_per_hour"]
    consumption = {
        # Distinguish free capacity (forecast basis) from consumption
        # (interpretive): net change over the last segment per hour.
        "net_change_gib": round(f_last - last_seg[0][1], 2),
        "span_hours": round(fit["span_hours"], 2),
        "avg_rate_gib_per_hour": round(
            (f_last - last_seg[0][1]) / max(fit["span_hours"], 1e-9), 4),
    }
    return {**base,
            "verdict": "STABLE" if stable else "FORECAST",
            "segment_fit": {
                "observations": fit["n"],
                "span_hours": round(fit["span_hours"], 2),
                "slope_gib_per_hour": round(fit["slope_gib_per_hour"], 5),
                "slope_2sigma_interval": [round(slope_lo, 5),
                                          round(slope_hi, 5)],
                "residual_sd_gib": round(fit["residual_sd"], 3),
                "band_2sigma_gib": round(band, 3),
                "last_observation_utc": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime(t_last)),
                "last_free_gib": round(f_last, 1),
            },
            "consumption": consumption,
            "time_to_gate": ({
                "hours": round(hours_to_gate, 1),
                "basis": "linear slope on last segment; band applies",
            } if hours_to_gate is not None and hours_to_gate > 0 else {
                "hours": None,
                "basis": "gate not projected to be crossed on this trend"
                if stable or fit["slope_gib_per_hour"] >= 0 else
                "gate line already below last observation",
            })}


def validate_window_pre(dirpath, now_s=None):
    """Re-verify PI-1 C1-C4 qualification before forecasting (mandate).
    Import-uses the validator: one authority, no drift."""
    return evw.validate_window(Path(dirpath), WINDOW_DAYS, now_s=now_s)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("snapshot_dir")
    ap.add_argument("--gate-gib", type=float, default=DEFAULT_GATE_GIB,
                    help="capacity gate line (default: validator's own)")
    ap.add_argument("--out", help="write JSON report to this path")
    args = ap.parse_args(argv)

    window, qualified = validate_window_pre(args.snapshot_dir)
    now_s = None
    series = load_series(args.snapshot_dir, now_s=now_s)
    gate = args.gate_gib
    if window.get("criteria", {}).get("c4_threshold_stability", {}) \
            .get("distinct_values"):
        vals = window["criteria"]["c4_threshold_stability"]["distinct_values"]
        gate = float(vals[0])
    result = forecast(series, gate, now_s=now_s)
    result["window_qualification"] = {
        "qualified": window.get("window_qualified", qualified),
        "validator_version": window.get("validator_version"),
        "snapshot_count": window.get("snapshot_count"),
        "malformed_count": window.get("malformed_count"),
        "criteria": {k: v.get("pass") for k, v in
                     window.get("criteria_results", {}).items()},
    }
    if not (window.get("window_qualified", qualified) or qualified):
        # Never forecast on an unqualified window, regardless of sample count.
        result = {**result, "verdict": "INSUFFICIENT_DATA",
                  "reason": "PI-1 evidence window does not qualify "
                            "(C1-C4); forecasting withheld"}
    out = json.dumps(result, indent=1, sort_keys=True)
    if args.out:
        Path(args.out).write_text(out + "\n")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
