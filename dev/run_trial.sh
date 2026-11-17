#!/bin/bash
# Manual practice-trial runner (grade-local needs Docker for python3.13, which
# this VM lacks): kit env server (process mode) + main.py + kit scorer.
set -u
KIT="$HOME/workspace/makefun/tiny-chess-01-kit"
BOT="$HOME/workspace/makefun/tiny-chess-entry"
T="${1:-0}"
PORT="${2:-18080}"
WORK="$BOT/dev/trial-$T-run"
rm -rf "$WORK"; mkdir -p "$WORK/state" "$WORK/scores"
MAKEFUN_ENV_DATA_DIR="$KIT/practice/trial-$T/input/env" MAKEFUN_STATE_DIR="$WORK/state" MAKEFUN_ENV_PORT=$PORT node "$KIT/program/env/server.mjs" > "$WORK/env.log" 2>&1 &
SRV=$!
for i in $(seq 1 50); do [ -f "$WORK/state/ready" ] && break; sleep 0.2; done
cat "$WORK/env.log"
cd "$BOT" && MAKEFUN_ENV_URL="http://127.0.0.1:$PORT" timeout 1500 python3 main.py > "$WORK/bot.log" 2>&1
echo "bot exit: $?"; cat "$WORK/bot.log"
kill -TERM $SRV 2>/dev/null; wait $SRV 2>/dev/null
MAKEFUN_OUTPUT_DIR="$WORK/state/export" MAKEFUN_REFERENCE_DIR="$KIT/practice/trial-$T/reference" MAKEFUN_SCORES_DIR="$WORK/scores" node "$KIT/program/scorer/score.mjs"
ls "$WORK/scores"
for f in "$WORK/scores"/*; do echo "--- $f"; head -c 1000 "$f"; echo; done
