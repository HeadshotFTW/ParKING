#!/bin/sh
set -eu

python api_app.py &
API_PID=$!

cleanup() {
    kill "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

python run.py
