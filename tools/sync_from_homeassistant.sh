#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
MANAGED_FILES_PATH="${SCRIPT_DIR}/managed_files.txt"
source "${SCRIPT_DIR}/sync_common.sh"
SOURCE_ROOT="${SOURCE_ROOT:-/homeassistant}"
TARGET_ROOT="${TARGET_ROOT:-${REPO_ROOT}}"
BACKUP_BASE="${BACKUP_BASE:-${REPO_ROOT}/.sync_backups/from-homeassistant}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${BACKUP_BASE}/${TIMESTAMP}"
TMP_ROOT="$(mktemp -d "${REPO_ROOT}/.sync-tmp.pull.XXXXXX")"
DRY_RUN=0
SHOW_DIFF=0
SHOW_STATUS=0
WITH_INVENTORY=1
SKIP_CONFIRM=0

cleanup() {
  rm -rf "${TMP_ROOT}"
}

on_error() {
  local exit_code=$?
  trap - ERR
  log "Sync failed. Restoring repo files from backup: ${BACKUP_DIR}"
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
      --with-inventory)
        WITH_INVENTORY=1
        ;;
      --no-inventory)
        WITH_INVENTORY=0
        ;;
      -y|--yes)
        SKIP_CONFIRM=1
        ;;
      -h|--help)
        cat <<'EOF'
Usage: sync_from_homeassistant.sh [--dry-run] [--diff] [--status] [--no-inventory] [--yes]

Options:
  --dry-run         Preview what would change without writing files
  --diff            Show file diffs for changed files
  --status          Show per-file changed/unchanged status
  --no-inventory    Skip automatic inventory export after pull
  --yes, -y         Skip confirmation prompt
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

commit_synced_files() {
  # Commit any files that were synced so the repo is clean before
  # the inventory exporter runs its own require_git_clean check.
  if command -v git > /dev/null 2>&1 && \
     git -C "${REPO_ROOT}" rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    if ! git -C "${REPO_ROOT}" diff --quiet HEAD -- 2>/dev/null || \
       ! git -C "${REPO_ROOT}" diff --cached --quiet HEAD -- 2>/dev/null; then
      log "Committing synced files to git"
      git -C "${REPO_ROOT}" add -A
      git -C "${REPO_ROOT}" commit -m "sync: pull from homeassistant $(date +%Y-%m-%dT%H:%M:%S)"
      git -C "${REPO_ROOT}" push || log "WARNING: git push failed — continuing without push"
    else
      log "No changes to commit (files were identical to repo)"
    fi
  fi
}

maybe_export_inventory() {
  [[ "${WITH_INVENTORY}" -eq 1 ]] || return 0
  if [[ -x "${SCRIPT_DIR}/export_ha_inventory.sh" ]]; then
    log "Exporting inventory snapshot into repo"
    "${SCRIPT_DIR}/export_ha_inventory.sh" -y "${TARGET_ROOT}/ha_device_inventory.json"
  else
    log "Inventory exporter not executable, skipping inventory export."
  fi
}

commit_inventory_files() {
  if ! command -v git > /dev/null 2>&1 || \
     ! git -C "${REPO_ROOT}" rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    return 0
  fi
  if ! git -C "${REPO_ROOT}" diff --quiet HEAD -- 2>/dev/null || \
     [[ -n "$(git -C "${REPO_ROOT}" ls-files --others --exclude-standard 2>/dev/null)" ]]; then
    log "Committing inventory files to git"
    git -C "${REPO_ROOT}" add -A
    git -C "${REPO_ROOT}" commit -m "inventory: update snapshot $(date +%Y-%m-%dT%H:%M:%S)"
    git -C "${REPO_ROOT}" push || log "WARNING: git push failed — continuing without push"
  fi
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
confirm_proceed "Pull configs from Home Assistant (${SOURCE_ROOT}) into repo? This will overwrite local files."
backup_targets "${TARGET_ROOT}" "${BACKUP_DIR}"
write_restore_script "${TARGET_ROOT}" "${BACKUP_DIR}"
sync_files
commit_synced_files
maybe_export_inventory
commit_inventory_files
trap - ERR
log "Sync completed successfully."
log "Backup created at ${BACKUP_DIR}"
log "Restore helper: ${BACKUP_DIR}/restore.sh"
