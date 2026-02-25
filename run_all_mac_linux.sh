#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "Starting Flask (VECTOR)..."
python3 -m venv .venv || true
source .venv/bin/activate
pip install -r requirements.txt
python app.py &

echo "Starting Next.js (site2.0)..."
cd inclusive_frontend/site2
npm install
npm run dev
