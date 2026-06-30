#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/sync_common.sh"
STORAGE_DIR="${STORAGE_DIR:-/homeassistant/.storage}"
SKIP_CONFIRM=0

# -------------------------------------------------------------------
# Parse positional and flag arguments
# -------------------------------------------------------------------
POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes)
      SKIP_CONFIRM=1
      ;;
    -h|--help)
      cat <<'EOF'
Usage: export_ha_inventory.sh [OUTPUT_PATH] [TEXT_OUTPUT_PATH] [NUMBER_MAP_PATH] [--yes]

Options:
  --yes, -y  Skip confirmation prompt
EOF
      exit 0
      ;;
    *)
      POSITIONAL_ARGS+=("$1")
      ;;
  esac
  shift
done

OUTPUT_PATH="${POSITIONAL_ARGS[0]:-${REPO_ROOT}/ha_device_inventory.json}"
TEXT_OUTPUT_PATH="${POSITIONAL_ARGS[1]:-$(dirname -- "${OUTPUT_PATH}")/inventory.txt}"
NUMBER_MAP_PATH="${POSITIONAL_ARGS[2]:-$(dirname -- "${OUTPUT_PATH}")/inventory_numbers.json}"

export SKIP_CONFIRM
require_git_clean "${REPO_ROOT}"
confirm_proceed "Export HA inventory into repo? This will overwrite ${OUTPUT_PATH}."

exec python3 "${SCRIPT_DIR}/export_ha_inventory.py" \
  --storage-dir "${STORAGE_DIR}" \
  --output "${OUTPUT_PATH}" \
  --text-output "${TEXT_OUTPUT_PATH}" \
  --number-map "${NUMBER_MAP_PATH}"

