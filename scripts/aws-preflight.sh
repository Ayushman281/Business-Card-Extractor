#!/usr/bin/env bash
# Run on the AWS server only. Does not create AWS resources or load Qwen.
set -euo pipefail
if [[ "${1:-}" != "--aws-only" ]]; then
  echo "Usage on the AWS server: bash scripts/aws-preflight.sh --aws-only" >&2
  exit 2
fi
for command in docker nvidia-smi; do
  command -v "$command" >/dev/null || { echo "Missing: $command" >&2; exit 1; }
done
docker version
docker compose version
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
free -h
df -h .
echo "Verify at least 16 GiB GPU VRAM, about 16 GiB host RAM and 60 GiB free disk for this deployment."
echo "Run Docker, CUDA and model checks from docs/aws-deployment.md before public access."
