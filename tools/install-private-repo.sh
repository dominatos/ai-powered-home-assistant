#!/usr/bin/env bash
set -Eeuo pipefail

# This script clones the template repo, renames files, and pushes to your private repo.
# Run it from anywhere — it creates the directory for you.

usage() {
  cat <<'EOF'
Usage: install-private-repo.sh <your-private-repo-url>

Clones the template repo, renames files, and pushes to your private repo.

Example:
  bash <(curl -s https://raw.githubusercontent.com/<TEMPLATE_ORG>/ai-powered-home-assistant/main/tools/install-private-repo.sh) git@github.com:username/my-home.git

EOF
  exit 0
}

die() { echo "Error: $*" >&2; exit 1; }

[[ $# -eq 1 ]] || usage
[[ "$1" == "-h" || "$1" == "--help" ]] && usage

PRIVATE_URL="$1"
TEMPLATE_URL="https://github.com/dominatos/ai-powered-home-assistant.git"
REPO_DIR="ai-powered-home-assistant"

command -v git > /dev/null 2>&1 || die "git is not installed"

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
git push --set-upstream origin main --force

echo ""
echo "Done! Your repo is ready at $(pwd)"
echo "Next: Open HOUSE_CONTEXT.md and document your house."
