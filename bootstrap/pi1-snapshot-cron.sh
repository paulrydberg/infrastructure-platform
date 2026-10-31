#!/bin/bash
# PI-1 snapshot scheduler wrapper (infrastructure-platform).
#
# PURPOSE: deterministic wrapper around platform_state_collector.py suitable
# for cron/launchd execution. NOT ACTIVATED — installing/enabling any
# scheduler entry requires explicit operator authorization (ADR-0012 gate).
# When authorized, the proposed crontab line is:
#
#   # infrastructure-platform: PI-1 platform-state snapshot (deterministic; no inference)
#   17 * * * * /Users/macmini/.hermes/projects/infrastructure-platform/bootstrap/pi1-snapshot-cron.sh >> $HOME/.infrastructure-platform/pi1-snapshot-cron.log 2>&1
#
# Design:
#   - lockfile-guarded (overlapping runs skip, not queue)
#   - snapshot JSON stored under ~/.infrastructure-platform/pi1-snapshots/
#     named pi1-YYYYMMDD-HHMMSSZ.json (UTC, sortable, collision-free)
#   - malformed/failed collection leaves a .failed marker with stderr; the
#     snapshot file is still written when structurally valid (nulls are data)
#   - retention: 90 days, enforced here (delete older than 90d on each run)
#   - exit codes: 0 ok/skip; 1 collection failed (logged, non-fatal for cron)
set -u
REPO="/Users/macmini/.hermes/projects/infrastructure-platform"
OUT_DIR="$HOME/.infrastructure-platform/pi1-snapshots"
LOCK="/tmp/pi1-snapshot.lock"
LOG_TAG="[pi1-cron]"
COLLECTOR="$REPO/bootstrap/platform_state_collector.py"
RETENTION_DAYS=90

mkdir -p "$OUT_DIR"

# ── concurrency: skip if another instance is running ──
if [ -e "$LOCK" ]; then
  LOCK_PID=$(cat "$LOCK" 2>/dev/null)
  if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $LOG_TAG skip: instance $LOCK_PID still running"
    exit 0
  fi
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $LOG_TAG stale lock (pid $LOCK_PID gone) — removing"
  rm -f "$LOCK"
fi
echo $$ > "$LOCK"
trap 'rm -f "$LOCK"' EXIT

# ── collect ──
STAMP=$(date -u +%Y%m%d-%H%M%SZ)
OUT="$OUT_DIR/pi1-$STAMP.json"
ERRTMP=$(mktemp)
if python3 "$COLLECTOR" > "$OUT" 2> "$ERRTMP"; then
  # structural sanity: must be JSON with collected_at_utc
  if python3 -c "import json,sys; s=json.load(open('$OUT')); assert s.get('collected_at_utc')" 2> /dev/null; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $LOG_TAG ok: $(basename "$OUT")"
    # probe errors are DATA (nulls recorded) — log them for visibility
    python3 -c "
import json
s = json.load(open('$OUT'))
errs = (s.get('provenance') or {}).get('probe_errors') or []
if errs:
    print('$(date -u +%Y-%m-%dT%H:%M:%SZ) $LOG_TAG probe_errors:', '; '.join(errs))
"
  else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $LOG_TAG FAILED: structurally invalid snapshot -> $(basename "$OUT").failed"
    mv "$OUT" "$OUT.failed"
    mv "$ERRTMP" "$OUT.failed.stderr" 2> /dev/null
    exit 1
  fi
else
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $LOG_TAG FAILED: collector exit $? -> $(basename "$OUT").failed"
  [ -s "$OUT" ] && mv "$OUT" "$OUT.failed"
  mv "$ERRTMP" "$OUT.failed.stderr" 2> /dev/null
  exit 1
fi
rm -f "$ERRTMP"

# ── retention ──
find "$OUT_DIR" -name "pi1-*.json" -mtime +$RETENTION_DAYS -delete 2> /dev/null
find "$OUT_DIR" -name "*.failed*" -mtime +$RETENTION_DAYS -delete 2> /dev/null
exit 0
