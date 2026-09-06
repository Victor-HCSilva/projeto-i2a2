#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"

if [[ -f /app/requirements.txt ]]; then
	REQUIREMENTS_FILE=/app/requirements.txt
fi

python -m pip install --upgrade pip
python -m pip install -r "${REQUIREMENTS_FILE}"
