#!/usr/bin/env bash
set -euo pipefail
echo "Deploying Library P0 Run13..."
docker compose up -d --build
echo "Deployed. Health: http://localhost:8000/api/health"
