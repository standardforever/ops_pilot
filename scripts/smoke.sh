#!/usr/bin/env sh
set -eu

base_url="${1:-http://127.0.0.1:8000}"
script_directory=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)

exec python3 "${script_directory}/smoke.py" "${base_url}"
