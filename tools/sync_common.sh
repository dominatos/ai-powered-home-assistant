#!/usr/bin/env bash
set -Eeuo pipefail

MANAGED_FILES_PATH="${MANAGED_FILES_PATH:-}"

log() {
  printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"
}

die() {
  printf '%s\n' "$*" >&2
  exit 1
}

# ---------------------------------------------------------------------------
# Git safety: abort if the repo has uncommitted changes or unpushed commits
# ---------------------------------------------------------------------------
require_git_clean() {
  local repo_dir="${1:-${REPO_ROOT:-.}}"

  if ! command -v git >/dev/null 2>&1; then
    log "WARNING: git not found — skipping repo-sync check."
    return 0
  fi

  if ! git -C "${repo_dir}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    log "WARNING: ${repo_dir} is not a git repo — skipping repo-sync check."
    return 0
  fi

  # Uncommitted changes (staged or unstaged)
  if ! git -C "${repo_dir}" diff --quiet HEAD -- 2>/dev/null || \
     ! git -C "${repo_dir}" diff --cached --quiet HEAD -- 2>/dev/null; then
    die "ERROR: Repository has uncommitted changes. Commit or stash before syncing."
  fi

  # Untracked files (excluding ignored)
  local untracked
  untracked="$(git -C "${repo_dir}" ls-files --others --exclude-standard 2>/dev/null)"
  if [[ -n "${untracked}" ]]; then
    log "WARNING: Untracked files detected (not blocking sync):"
    printf '  %s\n' ${untracked}
  fi

  # Unpushed / unpulled commits
  local upstream
  upstream="$(git -C "${repo_dir}" rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || true)"
  if [[ -n "${upstream}" ]]; then
    git -C "${repo_dir}" fetch --quiet 2>/dev/null || true
    local ahead behind
    ahead="$(git -C "${repo_dir}" rev-list --count "${upstream}"..HEAD 2>/dev/null || echo 0)"
    behind="$(git -C "${repo_dir}" rev-list --count HEAD.."${upstream}" 2>/dev/null || echo 0)"
    if [[ "${ahead}" -gt 0 ]]; then
      die "ERROR: Repository has ${ahead} unpushed commit(s) ahead of ${upstream}. Push before syncing."
    fi
    if [[ "${behind}" -gt 0 ]]; then
      log "Repository is ${behind} commit(s) behind ${upstream}. Pulling…"
      git -C "${repo_dir}" pull --ff-only 2>/dev/null \
        || die "ERROR: Could not fast-forward to ${upstream}. Resolve manually before syncing."
    fi
  else
    log "WARNING: No upstream tracking branch — cannot verify push status."
  fi

  log "Git repo is clean and in sync."
}

# ---------------------------------------------------------------------------
# Interactive confirmation prompt (skipped with --yes / -y or non-TTY)
# ---------------------------------------------------------------------------
confirm_proceed() {
  local message="${1:-Proceed?}"
  local skip_confirm="${SKIP_CONFIRM:-0}"

  if [[ "${skip_confirm}" -eq 1 ]]; then
    return 0
  fi

  if [[ ! -t 0 ]]; then
    die "ERROR: Non-interactive shell and --yes not specified. Aborting."
  fi

  printf '\n%s [y/N] ' "${message}"
  local answer
  read -r answer
  case "${answer}" in
    [yY]|[yY][eE][sS]) return 0 ;;
    *) die "Aborted by user." ;;
  esac
}

require_file() {
  local path=$1
  [[ -f "${path}" ]] || die "Missing required file: ${path}"
}

load_managed_files() {
  [[ -n "${MANAGED_FILES_PATH}" ]] || die "MANAGED_FILES_PATH is not set"
  require_file "${MANAGED_FILES_PATH}"

  FILES=()
  while IFS= read -r rel || [[ -n "${rel}" ]]; do
    [[ -n "${rel}" ]] || continue
    [[ "${rel}" == \#* ]] && continue
    FILES+=("${rel}")
  done < "${MANAGED_FILES_PATH}"

  [[ ${#FILES[@]} -gt 0 ]] || die "Managed file list is empty: ${MANAGED_FILES_PATH}"
}

detect_yaml_validation() {
  if command -v python3 >/dev/null 2>&1 && python3 -c 'import yaml' >/dev/null 2>&1; then
    CAN_VALIDATE_YAML=1
  else
    CAN_VALIDATE_YAML=0
    log "python3+PyYAML not available. YAML syntax validation will be skipped."
  fi
}

validate_yaml_file() {
  local file_path=$1
  [[ "${CAN_VALIDATE_YAML:-0}" -eq 1 ]] || return 0
  python3 - "${file_path}" <<'PY'
import pathlib
import sys
import yaml

class HomeAssistantLoader(yaml.SafeLoader):
    pass

def construct_ha_tag(loader, tag_suffix, node):
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_scalar(node)

HomeAssistantLoader.add_multi_constructor("!", construct_ha_tag)
yaml.load(pathlib.Path(sys.argv[1]).read_text(), Loader=HomeAssistantLoader)
PY
}

sha256_of_file() {
  local file_path=$1
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${file_path}" | awk '{print $1}'
  else
    shasum -a 256 "${file_path}" | awk '{print $1}'
  fi
}

files_differ() {
  local left=$1 right=$2
  [[ -e "${left}" ]] || return 0
  [[ -e "${right}" ]] || return 0
  [[ "$(sha256_of_file "${left}")" != "$(sha256_of_file "${right}")" ]]
}

print_diff() {
  local left=$1 right=$2 rel=$3
  if command -v git >/dev/null 2>&1; then
    git --no-pager diff --no-index -- "${left}" "${right}" || true
  elif command -v diff >/dev/null 2>&1; then
    diff -u --label "old/${rel}" --label "new/${rel}" "${left}" "${right}" || true
  else
    log "No diff tool available for ${rel}"
  fi
}

ensure_requirements() {
  local root rel path
  root=$1
  for rel in "${FILES[@]}"; do
    path="${root}/${rel}"
    [[ -f "${path}" ]] || die "Missing required file: ${path}"
  done
}

backup_targets() {
  local target_root=$1 backup_dir=$2 rel target_path backup_path
  mkdir -p "${backup_dir}/files"
  : > "${backup_dir}/missing.list"

  for rel in "${FILES[@]}"; do
    target_path="${target_root}/${rel}"
    backup_path="${backup_dir}/files/${rel}"
    if [[ -e "${target_path}" ]]; then
      mkdir -p "$(dirname "${backup_path}")"
      cp -a "${target_path}" "${backup_path}"
    else
      printf '%s\n' "${rel}" >> "${backup_dir}/missing.list"
    fi
  done
}

restore_targets() {
  local target_root=$1 backup_dir=$2 rel source_backup target_path
  [[ -d "${backup_dir}" ]] || return 0

  while IFS= read -r rel; do
    [[ -n "${rel}" ]] || continue
    rm -f "${target_root}/${rel}"
  done < "${backup_dir}/missing.list"

  for rel in "${FILES[@]}"; do
    source_backup="${backup_dir}/files/${rel}"
    target_path="${target_root}/${rel}"
    if [[ -e "${source_backup}" ]]; then
      mkdir -p "$(dirname "${target_path}")"
      cp -a "${source_backup}" "${target_path}"
    fi
  done
}

write_restore_script() {
  local target_root=$1 backup_dir=$2 rel
  {
    printf '#!/usr/bin/env bash\n'
    printf 'set -Eeuo pipefail\n\n'
    printf 'TARGET_ROOT="${1:-%s}"\n' "${target_root}"
    printf 'BACKUP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"\n\n'
    printf 'while IFS= read -r rel; do\n'
    printf '  [[ -n "${rel}" ]] || continue\n'
    printf '  rm -f "${TARGET_ROOT}/${rel}"\n'
    printf 'done < "${BACKUP_DIR}/missing.list"\n\n'
    printf "while IFS= read -r rel; do\n"
    printf '  [[ -n "${rel}" ]] || continue\n'
    printf '  if [[ -e "${BACKUP_DIR}/files/${rel}" ]]; then\n'
    printf '    mkdir -p "$(dirname "${TARGET_ROOT}/${rel}")"\n'
    printf '    cp -a "${BACKUP_DIR}/files/${rel}" "${TARGET_ROOT}/${rel}"\n'
    printf '  fi\n'
    printf "done <<'FILES'\n"
    for rel in "${FILES[@]}"; do
      printf '%s\n' "${rel}"
    done
    printf "FILES\n\n"
    printf "printf 'Restored files into %%s using backup %%s\\n' \"\${TARGET_ROOT}\" \"\${BACKUP_DIR}\"\n"
  } > "${backup_dir}/restore.sh"
  chmod +x "${backup_dir}/restore.sh"
}

summarize_changes() {
  local source_root=$1 target_root=$2 rel source_path target_path changed=0
  log "Managed files:"
  for rel in "${FILES[@]}"; do
    source_path="${source_root}/${rel}"
    target_path="${target_root}/${rel}"
    if [[ ! -e "${target_path}" ]]; then
      printf '  [NEW] %s\n' "${rel}"
      changed=1
    elif files_differ "${source_path}" "${target_path}"; then
      printf '  [CHANGED] %s\n' "${rel}"
      changed=1
    else
      printf '  [UNCHANGED] %s\n' "${rel}"
    fi
  done
  return "${changed}"
}
