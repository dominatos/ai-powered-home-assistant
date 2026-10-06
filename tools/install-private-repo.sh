#!/usr/bin/env bash
set -Eeuo pipefail

# This script clones the template repo, renames files, and pushes to your private repo.
# Run it from anywhere — it creates the directory for you.

usage() {
  cat <<'EOF'
Usage: install-private-repo.sh [--force] <your-private-repo-url>

Clones the template repo, renames files, and pushes to your private repo.

The target repository must be empty. Pass --force to overwrite an existing
history -- this is destructive and cannot be undone.

Example:
  bash <(curl -s https://raw.githubusercontent.com/<TEMPLATE_ORG>/ai-powered-home-assistant/main/tools/install-private-repo.sh) git@github.com:username/my-home.git

EOF
  exit "${1:-0}"
}

die() { echo "Error: $*" >&2; exit 1; }

# Strip HTTPS userinfo (user:pass@) from a URL for safe display.
redact_url() {
  local url="$1"
  # Match scheme://user:pass@host and replace with scheme://host
  if [[ "${url}" =~ ^(https?://)[^/]+@(.+)$ ]]; then
    echo "${BASH_REMATCH[1]}${BASH_REMATCH[2]}"
  else
    echo "${url}"
  fi
}

FORCE=0
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage 0 ;;
    -f|--force) FORCE=1 ;;
    *) ARGS+=("$1") ;;
  esac
  shift
done

[[ ${#ARGS[@]} -eq 1 ]] || usage 1

PRIVATE_URL="${ARGS[0]}"
TEMPLATE_URL="https://github.com/dominatos/ai-powered-home-assistant.git"
REPO_DIR="ai-powered-home-assistant"

command -v git > /dev/null 2>&1 || die "git is not installed"

# Refuse to clobber an existing history. `git push --force` here would
# silently destroy whatever the target repository already contained.
echo "Checking that the target repository is empty..."
if ! existing_refs="$(git ls-remote "${PRIVATE_URL}" 2>/dev/null)"; then
  die "Cannot reach $(redact_url "${PRIVATE_URL}") — check the URL and your SSH/HTTPS credentials."
fi
# Get the remote's default branch from the HEAD symref (e.g., "ref: refs/heads/main")
remote_default_branch=""
if ! head_ref="$(git ls-remote --symref "${PRIVATE_URL}" HEAD 2>/dev/null)"; then
  die "Cannot determine the remote's default branch from $(redact_url "${PRIVATE_URL}")"
fi
# Capture the complete branch name up to the whitespace field separator before HEAD
if [[ "${head_ref}" =~ ref:\ refs/heads/([^[:space:]]+) ]]; then
  remote_default_branch="${BASH_REMATCH[1]}"
fi
if [[ -n "${existing_refs}" ]]; then
  if [[ "${FORCE}" -ne 1 ]]; then
    echo "" >&2
    echo "The target repository already has branches:" >&2
    printf '%s\n' "${existing_refs}" | sed 's/^/  /' >&2
    echo "" >&2
    die "Refusing to overwrite an existing history.
Create an empty repository, or re-run with --force if you are certain you want
to discard everything currently in $(redact_url "${PRIVATE_URL}")."
  fi
  echo "WARNING: --force given; overwriting the existing history in $(redact_url "${PRIVATE_URL}")"
fi

echo "Cloning template..."
git clone "${TEMPLATE_URL}" "${REPO_DIR}"
cd "${REPO_DIR}"

echo "Setting up remote..."
git remote remove origin
git remote add origin "${PRIVATE_URL}"

echo "Renaming template files..."
for f in *.template.*; do
  if [ "$f" = "AUTOMATIONS_KB.template.md" ]; then
    mv "$f" "automations_kb.md"
  else
    mv "$f" "${f//.template./.}"
  fi
done

echo "Committing and pushing..."
git add .
git commit -m "Initial setup with renamed templates"
if [[ "${FORCE}" -eq 1 ]]; then
  # Validate the remote's default branch before any destructive operations.
  # GitHub (and other hosts) refuse to delete the current default branch,
  # so we must ensure it is main or master before proceeding.
  if [[ -z "${remote_default_branch}" ]]; then
    die "Could not determine the remote's default branch. Cannot safely force-push. Please set the default branch to main or master first."
  fi
  if [[ "${remote_default_branch}" != "main" && "${remote_default_branch}" != "master" ]]; then
    die "Remote default branch is '${remote_default_branch}', which is neither main nor master. Change the default branch to main or master before force-pushing."
  fi
  # Back up existing remote history with a complete mirror before destructive operations.
  # Stored in a persistent location outside REPO_DIR so the backup survives both
  # the force-push that replaces this work tree and a reboot (unlike /tmp).
  # Override with HA_REPO_BACKUP_DIR if desired.
  backup_root="${HA_REPO_BACKUP_DIR:-${HOME}/.local/share/ai-powered-home-assistant/backups}"
  if ! mkdir -p "${backup_root}"; then
    die "Cannot create backup directory ${backup_root}. Aborting before destructive push."
  fi
  if ! backup_dir="$(mktemp -d "${backup_root}/ha_repo_backup_XXXXXX")"; then
    die "Cannot create a backup directory under ${backup_root}. Aborting before destructive push."
  fi
  backup_mirror="${backup_dir}/remote_mirror.git"
  if ! git clone --mirror "${PRIVATE_URL}" "${backup_mirror}"; then
    rm -rf "${backup_dir}"
    die "Failed to create mirror backup of $(redact_url "${PRIVATE_URL}") at ${backup_mirror}. Aborting before destructive push."
  fi
  # Also save the ref list for quick inspection.
  printf '%s\n' "${existing_refs}" > "${backup_dir}/remote_refs.txt"
  echo "Backed up remote history to ${backup_mirror}"
  echo "Ref list saved to ${backup_dir}/remote_refs.txt"
  git push --set-upstream origin main --force
  if printf '%s\n' "${existing_refs}" | grep -q $'\trefs/heads/master$'; then
    git push origin main:master --force
  fi
  # Remove any remaining remote branches other than main/master
  while IFS=$'\t' read -r _hash ref; do
    branch="${ref#refs/heads/}"
    if [[ "${ref}" == refs/heads/* && "${branch}" != "main" && "${branch}" != "master" ]]; then
      if ! git push origin --delete "${branch}"; then
        die "Failed to delete remote branch ${branch}. Aborting; the remote still contains this branch."
      fi
    fi
  done <<< "${existing_refs}"
  # Remove all remote tags (--refs skips peeled entries for annotated tags)
  if ! tag_refs="$(git ls-remote --refs --tags origin 2>/dev/null)"; then
    die "Failed to list remote tags from $(redact_url "${PRIVATE_URL}"). Aborting; remote tags were not cleaned up."
  fi
  while IFS=$'\t' read -r _hash ref; do
    if [[ "${ref}" == refs/tags/* ]]; then
      tag="${ref#refs/tags/}"
      if ! git push origin --delete "refs/tags/${tag}"; then
        die "Failed to delete remote tag ${tag}. Aborting; the remote still contains this tag."
      fi
    fi
  done <<< "${tag_refs}"
else
  git push --set-upstream origin main
fi

echo ""
echo "Done! Your repo is ready at $(pwd)"
echo "Next: Open HOUSE_CONTEXT.md and document your house."
