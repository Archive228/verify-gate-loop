#!/usr/bin/env bash
# One command. No install, no API key, no network.
set -euo pipefail
cd "$(dirname "$0")"
exec python3 -m src.demo
