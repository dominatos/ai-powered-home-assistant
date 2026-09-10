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
  exit 0
}

die() { echo "Error: $*" >&2; exit 1; }

FORCE=0
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage ;;
    -f|--force) FORCE=1 ;;
    *) ARGS+=("$1") ;;
  esac
  shift
done

[[ ${#ARGS[@]} -eq 1 ]] || usage

PRIVATE_URL="${ARGS[0]}"
TEMPLATE_URL="https://github.com/dominatos/ai-powered-home-assistant.git"
REPO_DIR="ai-powered-home-assistant"

command -v git > /dev/null 2>&1 || die "git is not installed"

# Refuse to clobber an existing history. `git push --force` here would
# silently destroy whatever the target repository already contained.
echo "Checking that the target repository is empty..."
existing_refs="$(git ls-remote --heads "${PRIVATE_URL}" 2>/dev/null || true)"
if [[ -n "${existing_refs}" ]]; then
  if [[ "${FORCE}" -ne 1 ]]; then
    echo "" >&2
    echo "The target repository already has branches:" >&2
    printf '%s\n' "${existing_refs}" | sed 's/^/  /' >&2
    echo "" >&2
    die "Refusing to overwrite an existing history.
Create an empty repository, or re-run with --force if you are certain you want
to discard everything currently in ${PRIVATE_URL}."
  fi
  echo "WARNING: --force given; overwriting the existing history in ${PRIVATE_URL}"
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
  git push --set-upstream origin main --force
else
  git push --set-upstream origin main
fi

echo ""
echo "Done! Your repo is ready at $(pwd)"
echo "Next: Open HOUSE_CONTEXT.md and document your house."
