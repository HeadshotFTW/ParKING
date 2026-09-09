#!/bin/sh
set -eu
# pokreni API u backgroundu
python api_app.py &
API_PID=$!
# cleanup nakon prekida procesa
cleanup() {
    kill "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

python run.py
