#!/usr/bin/env bash
# pull_debug_files.sh
# ====================
# Securely pulls Home Assistant logs and automation traces from a remote
# HAOS instance via SCP for local inspection and AI-assisted debugging.
#
# Usage:
#   ./tools/pull_debug_files.sh [--dry-run]
#
# Configuration (via environment variables):
#   HA_HOST   — IP or hostname of your HA instance (required)
#   HA_USER   — SSH user on the HA instance     (default: root)
#   HA_PORT   — SSH port                         (default: 22)
#   HA_CONFIG — Path to HA config dir on server  (default: /config)
#
# The files are saved to the local temp/ directory (gitignored).
# Requires SSH key-based auth or will prompt for password.

set -Eeuo pipefail

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  echo "DRY RUN: Would fetch debug files, but no changes will be made."
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
TEMP_DIR="${REPO_ROOT}/temp"

HA_HOST="${HA_HOST:-}"
HA_USER="${HA_USER:-root}"
HA_PORT="${HA_PORT:-22}"
HA_CONFIG="${HA_CONFIG:-/config}"

if [[ -z "${HA_HOST}" ]]; then
  echo "Error: HA_HOST is not set."
  echo "  Set it via environment variable:  HA_HOST=192.168.1.100 ./tools/pull_debug_files.sh"
  echo "  Or export it in your shell:       export HA_HOST=192.168.1.100"
  exit 1
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo ""
  echo "Would fetch:"
  echo "  - ${HA_CONFIG}/home-assistant.log -> ${TEMP_DIR}/home-assistant.log"
  echo "  - ${HA_CONFIG}/.storage/trace.saved_traces -> ${TEMP_DIR}/trace.saved_traces/"
  exit 0
fi

mkdir -p "${TEMP_DIR}"
chmod 700 "${TEMP_DIR}"

echo "Fetching debug files from ${HA_USER}@${HA_HOST}:${HA_CONFIG} ..."
echo "(Uses your SSH key or will prompt for password)"
echo ""

SCP_OPTS="-o StrictHostKeyChecking=accept-new -P ${HA_PORT}"

# Download the main log file
echo "→ home-assistant.log"
scp ${SCP_OPTS} \
  "${HA_USER}@${HA_HOST}:${HA_CONFIG}/home-assistant.log" \
  "${TEMP_DIR}/" \
  || echo "  WARNING: Failed to fetch home-assistant.log"

# Download saved automation traces
echo "→ .storage/trace.saved_traces"
TRACE_TEMP="${TEMP_DIR}/trace.saved_traces_tmp"
rm -rf "${TRACE_TEMP}"
scp -r ${SCP_OPTS} \
  "${HA_USER}@${HA_HOST}:${HA_CONFIG}/.storage/trace.saved_traces" \
  "${TRACE_TEMP}" \
  || { echo "  WARNING: Failed to fetch trace.saved_traces"; rm -rf "${TRACE_TEMP}"; }

# Replace existing traces only after successful download
if [ -d "${TRACE_TEMP}" ]; then
  rm -rf "${TEMP_DIR}/trace.saved_traces"
  mv "${TRACE_TEMP}" "${TEMP_DIR}/trace.saved_traces"
fi

echo ""
echo "Done! Files saved to: ${TEMP_DIR}/"
echo ""
echo "Next steps:"
echo "  1. Open temp/home-assistant.log and paste relevant error lines to the AI."
echo "  2. Or use the prompts/troubleshoot-trace.md prompt with a trace from"
echo "     temp/trace.saved_traces/<automation_id>."
