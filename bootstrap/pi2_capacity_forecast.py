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
# Discontinuity detection: a rate-normalized change in free space is
# material when the GiB/hour rate exceeds JUMP_GIB_PER_HOUR. This
# normalizes by the actual observation gap so that:
#   - plausible gradual consumption (e.g. 6 GiB/h over several hours)
#     is NOT a discontinuity;
#   - purgeable-space oscillations (~25-50 GiB in ~1h -> 25-50 GiB/h)
#     ARE discontinuities;
#   - the genuine 234 GiB release (1h -> 234 GiB/h) IS a discontinuity;
#   - future irregular gaps are handled correctly.
# Threshold chosen to separate plausible consumption (<=15 GiB/h) from
# purgeable releases (>25 GiB/h). The 2026-11-12 234 GiB/h release
# remains decisively detected. A 15 GiB outlier over 1h (15 GiB/h)
# is below this threshold and treated as an outlier, not a discontinuity.
# Zero/negative/extreme gaps are handled safely (rate = delta / max(gap_h, 1e-3)).
JUMP_GIB_PER_HOUR = 20.0
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
    """Extract free_disk_gib from snapshot. Returns float >= 0 or None if
    missing, null, negative, or non-numeric. None signals an excluded
    observation; the caller tracks exclusion counts and reasons."""
    host = snapshot.get("host") or {}
    v = host.get("free_disk_gib")
    if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0:
        return float(v)
    return None


def _free_gib_null(snapshot):
    """Check if free_disk_gib is present but null/explicitly None (permitted
    by schema). Returns True if the field exists and is None."""
    host = snapshot.get("host") or {}
    return "free_disk_gib" in host and host.get("free_disk_gib") is None


def load_series(dirpath, now_s=None):
    """Chronological [(epoch_s, free_gib)] from schema-valid snapshots in
    the trailing validator window. Malformed/duplicate/future-dated
    observations are dropped (conservatively) — the validator's counts
    remain the authoritative record of what was excluded. Returns
    (series, excluded_counts) where excluded_counts is a dict with
    'null_free_disk_gib' and 'invalid_free_disk_gib' counts."""
    records, _malformed = evw._load_snapshots(str(dirpath), WINDOW_DAYS,
                                              now_s=now_s)
    series = []
    excluded_null = 0
    excluded_invalid = 0
    if records:
        for r in records:
            rec = r.get("record") or {}
            if _free_gib_null(rec):
                excluded_null += 1
                continue
            f = _free_gib(rec)
            if f is not None:
                series.append((r["ts"], f))
            else:
                excluded_invalid += 1
    series.sort(key=lambda p: p[0])
    return series, {"null_free_disk_gib": excluded_null,
                    "invalid_free_disk_gib": excluded_invalid}


def detect_discontinuities(series):
    """Indices i where the rate-normalized change series[i] - series[i-1]
    is a material step change. Rate = delta_GiB / gap_hours; a rate >=
    JUMP_GIB_PER_HOUR marks a change of measured base, not ordinary
    consumption. Gap is the elapsed time between observations; zero,
    negative, or extreme gaps are clamped (rate = delta / max(gap_h, 1e-3)).
    This prevents:
      - plausible gradual consumption (e.g. 6 GiB/h over several hours)
        from being treated as a structural break;
      - purgeable-space oscillations (~25-50 GiB in ~1h -> 25-50 GiB/h)
        from being treated as continuous trend;
      - the genuine 234 GiB release (1h -> 234 GiB/h) from being missed.
    """
    out = []
    for i in range(1, len(series)):
        delta = series[i][1] - series[i - 1][1]
        gap_s = series[i][0] - series[i - 1][0]
        gap_h = max(gap_s / 3600.0, 1e-3)
        rate = abs(delta) / gap_h
        if rate > JUMP_GIB_PER_HOUR:
            out.append({"index": i, "at_utc": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(series[i][0])),
                "delta_gib": round(delta, 1),
                "gap_h": round(gap_h, 2),
                "rate_gib_per_hour": round(rate, 1)})
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


def forecast(series, excluded_counts, gate_gib, now_s=None):
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
                  "excluded_observations": excluded_counts,
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
        # Project from evaluation time (now), not from last observation,
        # so the reported remaining time is not stale.
        hours_to_gate = (f_last + fit["slope_gib_per_hour"] * (now - t_last) / 3600.0 - gate_gib) / -fit["slope_gib_per_hour"]
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


def backtest(series, gate_gib, now_s=None):
    """Chronological rolling-origin backtest on the last history segment.
    Each forecast origin uses only observations available at that origin.
    Returns a list of evaluation dicts with forecast error metrics.
    Respects discontinuity segmentation (origins only in the last segment).
    Returns empty dict if insufficient history for any evaluation.
    """
    last_seg, _ = segment(series, detect_discontinuities(series))
    if len(last_seg) < MIN_SAMPLES + 2:  # need train + at least 1 test
        return {}

    evaluations = []
    # Start from MIN_SAMPLES, increment by 1 observation each origin
    for i in range(MIN_SAMPLES, len(last_seg) - 1):
        train = last_seg[:i + 1]
        test = last_seg[i + 1]
        if len(train) < MIN_SAMPLES:
            continue

        fit = _fit(train)
        if fit["slope_gib_per_hour"] >= 0:
            # No declining trend to evaluate
            continue

        # Forecast from origin (train end) to test point
        origin_t = train[-1][0]
        origin_f = train[-1][1]
        gap_s = test[0] - origin_t
        if gap_s <= 0:
            continue
        gap_h = gap_s / 3600.0

        predicted = origin_f + fit["slope_gib_per_hour"] * (gap_s / 3600.0)
        actual = test[1]
        error_gib = predicted - actual
        error_pct = (error_gib / actual * 100) if actual > 0 else float("inf")

        evaluations.append({
            "origin_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                         time.gmtime(train[-1][0])),
            "train_observations": len(train),
            "gap_hours": round(gap_s / 3600.0, 2),
            "predicted_gib": round(predicted, 2),
            "actual_gib": round(test[1], 2),
            "error_gib": round(error_gib, 3),
            "error_pct": round(error_pct, 2),
        })

    if not evaluations:
        return {}

    # Aggregate metrics
    mae_gib = sum(abs(e["error_gib"]) for e in evaluations) / len(evaluations)
    mse_gib = sum(e["error_gib"] ** 2 for e in evaluations) / len(evaluations)
    rmse_gib = math.sqrt(mse_gib)
    mape = sum(abs(e["error_pct"]) for e in evaluations) / len(evaluations)

    return {
        "evaluations": evaluations,
        "summary": {
            "evaluation_count": len(evaluations),
            "mae_gib": round(mae_gib, 3),
            "rmse_gib": round(rmse_gib, 3),
            "mape_pct": round(mape, 2),
            "first_origin_utc": evaluations[0]["origin_utc"] if evaluations else None,
            "last_origin_utc": evaluations[-1]["origin_utc"] if evaluations else None,
        }
    }


def validate_window_pre(dirpath, now_s=None):
    """Re-verify PI-1 C1-C4 qualification before forecasting (mandate).
    Import-uses the validator: one authority, no drift."""
    return evw.validate_window(str(dirpath), WINDOW_DAYS, now_s=now_s)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("snapshot_dir")
    ap.add_argument("--gate-gib", type=float, default=DEFAULT_GATE_GIB,
                    help="capacity gate line (default: validator's own)")
    ap.add_argument("--out", help="write JSON report to this path")
    args = ap.parse_args(argv)

    window, qualified = validate_window_pre(args.snapshot_dir)
    now_s = None
    series, excluded_counts = load_series(args.snapshot_dir, now_s=now_s)
    gate = args.gate_gib
    if window.get("criteria", {}).get("c4_threshold_stability", {}) \
            .get("distinct_values"):
        vals = window["criteria"]["c4_threshold_stability"]["distinct_values"]
        gate = float(vals[0])
    result = forecast(series, excluded_counts, gate, now_s=now_s)
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