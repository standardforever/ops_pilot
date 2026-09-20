#!/usr/bin/env sh
set -eu

base_url="${1:-http://127.0.0.1:8000}"

curl --fail --silent --show-error "${base_url}/health/live" >/dev/null
curl --fail --silent --show-error "${base_url}/health/ready" >/dev/null

printf '%s\n' "OpsPilot smoke test passed: ${base_url}"

