#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
MANAGED_FILES_PATH="${SCRIPT_DIR}/managed_files.txt"
source "${SCRIPT_DIR}/sync_common.sh"
SOURCE_ROOT="${SOURCE_ROOT:-${REPO_ROOT}}"
TARGET_ROOT="${TARGET_ROOT:-/homeassistant}"
BACKUP_BASE="${BACKUP_BASE:-${REPO_ROOT}/.sync_backups/to-homeassistant}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${BACKUP_BASE}/${TIMESTAMP}"
TMP_ROOT="$(mktemp -d "${REPO_ROOT}/.sync-tmp.push.XXXXXX")"
DRY_RUN=0
SHOW_DIFF=0
SHOW_STATUS=0
SKIP_CONFIRM=0

cleanup() {
  rm -rf "${TMP_ROOT}"
}

on_error() {
  local exit_code=$?
  trap - ERR
  log "Sync failed. Restoring production files from backup: ${BACKUP_DIR}"
  restore_targets "${TARGET_ROOT}" "${BACKUP_DIR}" || true
  exit "${exit_code}"
}

trap cleanup EXIT
trap on_error ERR

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run)
        DRY_RUN=1
        ;;
      --diff)
        SHOW_DIFF=1
        ;;
      --status)
        SHOW_STATUS=1
        ;;
      -y|--yes)
        SKIP_CONFIRM=1
        ;;
      -h|--help)
        cat <<'EOF'
Usage: sync_to_homeassistant.sh [--dry-run] [--diff] [--status] [--yes]

Options:
  --dry-run  Preview what would change without writing files
  --diff     Show file diffs for changed files
  --status   Show per-file changed/unchanged status
  --yes, -y  Skip confirmation prompt
EOF
        exit 0
        ;;
      *)
        die "Unknown option: $1"
        ;;
    esac
    shift
  done
}

preview_changes() {
  local rel source_path target_path
  local changed=0

  for rel in "${FILES[@]}"; do
    source_path="${SOURCE_ROOT}/${rel}"
    target_path="${TARGET_ROOT}/${rel}"
    if [[ ! -e "${target_path}" ]]; then
      changed=1
      if [[ "${SHOW_DIFF}" -eq 1 ]]; then
        log "New file would be created: ${rel}"
      fi
    elif files_differ "${source_path}" "${target_path}"; then
      changed=1
      if [[ "${SHOW_DIFF}" -eq 1 ]]; then
        print_diff "${target_path}" "${source_path}" "${rel}"
      fi
    fi
  done

  return "${changed}"
}

sync_files() {
  local rel source_path target_path tmp_path
  local synced_count=0 skipped_count=0

  for rel in "${FILES[@]}"; do
    source_path="${SOURCE_ROOT}/${rel}"
    target_path="${TARGET_ROOT}/${rel}"
    tmp_path="${TMP_ROOT}/${rel}.tmp"

    if [[ -e "${target_path}" ]] && ! files_differ "${source_path}" "${target_path}"; then
      ((skipped_count+=1))
      log "Unchanged, skipped ${rel}"
      continue
    fi

    mkdir -p "$(dirname "${tmp_path}")"
    cp -a "${source_path}" "${tmp_path}"
    case "${rel}" in
      *.yaml|*.yml)
        validate_yaml_file "${tmp_path}"
        ;;
    esac

    mkdir -p "$(dirname "${target_path}")"
    mv "${tmp_path}" "${target_path}"
    ((synced_count+=1))
    log "Synced ${rel}"
  done

  log "Changed files synced: ${synced_count}; unchanged skipped: ${skipped_count}"
}

parse_args "$@"
export SKIP_CONFIRM
load_managed_files
log "Syncing automation files from ${SOURCE_ROOT} into ${TARGET_ROOT}"
require_git_clean "${REPO_ROOT}"
ensure_requirements "${SOURCE_ROOT}"
detect_yaml_validation
if [[ "${SHOW_STATUS}" -eq 1 ]]; then
  summarize_changes "${SOURCE_ROOT}" "${TARGET_ROOT}" || true
fi
preview_changes || true
if [[ "${DRY_RUN}" -eq 1 ]]; then
  log "Dry run complete. No files were written."
  trap - ERR
  exit 0
fi
confirm_proceed "Push configs to Home Assistant (${TARGET_ROOT})? This will overwrite production files."
backup_targets "${TARGET_ROOT}" "${BACKUP_DIR}"
write_restore_script "${TARGET_ROOT}" "${BACKUP_DIR}"
sync_files
trap - ERR
log "Sync completed successfully."
log "Backup created at ${BACKUP_DIR}"
log "Restore helper: ${BACKUP_DIR}/restore.sh"
