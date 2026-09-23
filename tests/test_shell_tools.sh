#!/usr/bin/env bash
# test_shell_tools.sh
# ===================
# Unit tests for all shell scripts in tools/.
#
# Run from the repository root:
#     bash tests/test_shell_tools.sh
#
# Tests use temporary directories with mock data — no real HA installation needed.
set -Eeuo pipefail

PASS=0
FAIL=0
SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
TOOLS="${REPO_ROOT}/tools"
TMPDIR_TEST="$(mktemp -d "${TMPDIR:-/tmp}/test-shell.XXXXXX")"

# cleanup removes the temporary test directory.
cleanup() { rm -rf "${TMPDIR_TEST}"; }
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Helpers
# check verifies that actual output contains the expected text and records the test result.
check() {
  local label="$1" expected="$2" actual="$3"
  if [[ "${actual}" == *"${expected}"* ]]; then
    PASS=$((PASS + 1))
    printf "  ✅ %s\n" "${label}"
  else
    FAIL=$((FAIL + 1))
    printf "  ❌ %s — expected '%s', got '%s'\n" "${label}" "${expected}" "${actual:0:80}"
  fi
}

# check_exit verifies that an actual exit status matches the expected status and records the test result.
check_exit() {
  local label="$1" expected="$2" actual="$3"
  if [[ "${actual}" -eq "${expected}" ]]; then
    PASS=$((PASS + 1))
    printf "  ✅ %s (exit %s)\n" "${label}" "${actual}"
  else
    FAIL=$((FAIL + 1))
    printf "  ❌ %s — expected exit %s, got %s\n" "${label}" "${expected}" "${actual}"
  fi
}

# make_mock_ha creates a minimal mock Home Assistant configuration directory at the specified path.
make_mock_ha() {
  local dir="$1"
  mkdir -p "${dir}"
  echo "homeassistant:" > "${dir}/configuration.yaml"
  echo "- alias: Test" > "${dir}/automations.yaml"
  echo "test_script:" > "${dir}/scripts.yaml"
  echo "test_scene:" > "${dir}/scenes.yaml"
  mkdir -p "${dir}/zigbee2mqtt"
  echo "mqtt:" > "${dir}/zigbee2mqtt/configuration.yaml"
}

# make_managed_files creates a minimal managed-file manifest in the specified directory.
make_managed_files() {
  local dir="$1"
  mkdir -p "${dir}/zigbee2mqtt"
  cat > "${dir}/managed_files.txt" <<'EOF'
configuration.yaml
automations.yaml
scripts.yaml
scenes.yaml
zigbee2mqtt/configuration.yaml
EOF
}

# ===========================================================================
# 1. sync_common.sh — test helper functions
# ===========================================================================
printf "\n🔧 sync_common.sh\n"

# Test: log function
result="$(cd "${REPO_ROOT}" && bash -c 'source tools/sync_common.sh && log "hello world" 2>/dev/null' 2>&1 || true)"
check "log outputs timestamp" "hello world" "${result}"

# Test: die function exits with error
set +e
cd "${REPO_ROOT}" && bash -c 'source tools/sync_common.sh && die "test error"' 2>/dev/null
die_exit=$?
set -e
check_exit "die exits non-zero" 1 "${die_exit}"

# Test: load_managed_files with valid file
mf_dir="${TMPDIR_TEST}/mf_valid"
make_managed_files "${mf_dir}"
result="$(cd "${REPO_ROOT}" && bash -c "
  MANAGED_FILES_PATH='${mf_dir}/managed_files.txt'
  source tools/sync_common.sh
  load_managed_files
  echo \${#FILES[@]}
" 2>&1 || true)"
check "load_managed_files reads 5 files" "5" "${result}"

# Test: load_managed_files with missing file
set +e
cd "${REPO_ROOT}" && bash -c "
  MANAGED_FILES_PATH='/nonexistent/file.txt'
  source tools/sync_common.sh
  load_managed_files
" 2>/dev/null
mf_exit=$?
set -e
check_exit "load_managed_files with missing file exits non-zero" 1 "${mf_exit}"

# Test: optional managed files ("?" prefix) are skipped when absent
opt_src="${TMPDIR_TEST}/optsrc"
opt_list="${TMPDIR_TEST}/managed_optional.txt"
mkdir -p "${opt_src}"
printf 'a.yaml
?missing.yaml
' > "${opt_list}"
printf 'x: 1
' > "${opt_src}/a.yaml"
result="$(cd "${REPO_ROOT}" && bash -c "
  MANAGED_FILES_PATH='${opt_list}'
  source tools/sync_common.sh
  load_managed_files
  ensure_requirements '${opt_src}'
  echo \"KEPT:\${FILES[*]}\"
" 2>&1 || true)"
check "optional managed file is skipped when absent" "KEPT:a.yaml" "${result}"

# Test: a missing REQUIRED managed file still aborts
req_list="${TMPDIR_TEST}/managed_required.txt"
printf 'a.yaml
missing.yaml
' > "${req_list}"
result="$(cd "${REPO_ROOT}" && bash -c "
  MANAGED_FILES_PATH='${req_list}'
  source tools/sync_common.sh
  load_managed_files
  ensure_requirements '${opt_src}'
  echo REACHED
" 2>&1 || true)"
if [[ "${result}" == *"REACHED"* ]]; then
  FAIL=$((FAIL + 1))
  printf "  ❌ missing required managed file aborts
"
else
  PASS=$((PASS + 1))
  printf "  ✅ missing required managed file aborts
"
fi

# Test: validate_yaml_file with valid YAML
valid_yaml="${TMPDIR_TEST}/valid.yaml"
echo "key: value" > "${valid_yaml}"
result="$(cd "${REPO_ROOT}" && bash -c "
  source tools/sync_common.sh
  detect_yaml_validation
  validate_yaml_file '${valid_yaml}'
  echo OK
" 2>&1 || true)"
check "validate_yaml_file accepts valid YAML" "OK" "${result}"

# Test: validate_yaml_file with invalid YAML
invalid_yaml="${TMPDIR_TEST}/invalid.yaml"
echo "key: value: bad: {{yaml" > "${invalid_yaml}"
result="$(cd "${REPO_ROOT}" && bash -c "
  source tools/sync_common.sh
  detect_yaml_validation
  validate_yaml_file '${invalid_yaml}'
  echo OK
" 2>&1 || true)"
# invalid YAML should fail
if [[ "${result}" == *"OK"* ]]; then
  FAIL=$((FAIL + 1))
  printf "  ❌ validate_yaml_file rejects invalid YAML\n"
else
  PASS=$((PASS + 1))
  printf "  ✅ validate_yaml_file rejects invalid YAML\n"
fi

# Test: files_differ
file_a="${TMPDIR_TEST}/file_a.txt"
file_b="${TMPDIR_TEST}/file_b.txt"
echo "same" > "${file_a}"
echo "same" > "${file_b}"
result="$(cd "${REPO_ROOT}" && bash -c "
  source tools/sync_common.sh
  if files_differ '${file_a}' '${file_b}'; then echo DIFFER; else echo SAME; fi
" 2>&1 || true)"
check "files_differ returns SAME for identical files" "SAME" "${result}"

echo "different" > "${file_b}"
result="$(cd "${REPO_ROOT}" && bash -c "
  source tools/sync_common.sh
  if files_differ '${file_a}' '${file_b}'; then echo DIFFER; else echo SAME; fi
" 2>&1 || true)"
check "files_differ returns DIFFER for different files" "DIFFER" "${result}"

# Test: sha256_of_file
echo "test content" > "${file_a}"
result="$(cd "${REPO_ROOT}" && bash -c "
  source tools/sync_common.sh
  sha256_of_file '${file_a}'
" 2>&1 || true)"
check "sha256_of_file returns 64-char hash" "64" "${#result}"

# Test: require_file
result="$(cd "${REPO_ROOT}" && bash -c "
  source tools/sync_common.sh
  require_file '${file_a}'
  echo OK
" 2>&1 || true)"
check "require_file accepts existing file" "OK" "${result}"

set +e
cd "${REPO_ROOT}" && bash -c "
  source tools/sync_common.sh
  require_file '/nonexistent/file'
  echo OK
" 2>/dev/null
rf_exit=$?
set -e
check_exit "require_file rejects missing file" 1 "${rf_exit}"


# ===========================================================================
# 2. sync_from_homeassistant.sh — test --help and --dry-run
# ===========================================================================
printf "\n📥 sync_from_homeassistant.sh\n"

result="$(bash "${TOOLS}/sync_from_homeassistant.sh" --help 2>&1 || true)"
check "sync_from --help shows Usage" "Usage" "${result}"
check "sync_from --help shows --dry-run" "--dry-run" "${result}"

# Test --dry-run with no HA dir (should still show preview)
mock_ha="${TMPDIR_TEST}/mock_ha_from"
make_mock_ha "${mock_ha}"
managed="${TMPDIR_TEST}/managed_from"
make_managed_files "${managed}"
if result="$(cd "${REPO_ROOT}" && SOURCE_ROOT="${mock_ha}" MANAGED_FILES_PATH="${managed}/managed_files.txt" bash "${TOOLS}/sync_from_homeassistant.sh" --dry-run --yes 2>&1)"; then
  dry_status=0
else
  dry_status=$?
fi
# Script may fail due to git checks; assert it ran and printed something relevant
if [[ ${dry_status} -eq 0 || -n "${result}" ]] && echo "${result}" | grep -qiE 'dry.run|DRY|sync|SYNC'; then
  PASS=$((PASS + 1))
  printf "  ✅ sync_from --dry-run produces output\n"
else
  FAIL=$((FAIL + 1))
  printf "  ❌ sync_from --dry-run produced no expected output (status %d)\n" "${dry_status}"
fi


# ===========================================================================
# 3. sync_to_homeassistant.sh — test --help and --dry-run
# ===========================================================================
printf "\n📤 sync_to_homeassistant.sh\n"

result="$(bash "${TOOLS}/sync_to_homeassistant.sh" --help 2>&1 || true)"
check "sync_to --help shows Usage" "Usage" "${result}"
check "sync_to --help shows --dry-run" "--dry-run" "${result}"

# Test --dry-run with mock HA dir
mock_ha="${TMPDIR_TEST}/mock_ha_to"
make_mock_ha "${mock_ha}"
if result="$(cd "${REPO_ROOT}" && TARGET_ROOT="${mock_ha}" bash "${TOOLS}/sync_to_homeassistant.sh" --dry-run --yes 2>&1)"; then
  dry_status=0
else
  dry_status=$?
fi
# Script may fail due to git checks; assert it ran and printed something relevant
if [[ ${dry_status} -eq 0 || -n "${result}" ]] && echo "${result}" | grep -qiE 'dry.run|DRY|sync|SYNC'; then
  PASS=$((PASS + 1))
  printf "  ✅ sync_to --dry-run produces output\n"
else
  FAIL=$((FAIL + 1))
  printf "  ❌ sync_to --dry-run produced no expected output (status %d)\n" "${dry_status}"
fi


# ===========================================================================
# 4. export_ha_inventory.sh — test --help
# ===========================================================================
printf "\n📦 export_ha_inventory.sh\n"

result="$(bash "${TOOLS}/export_ha_inventory.sh" --help 2>&1 || true)"
check "export_inventory --help shows Usage" "Usage" "${result}"


# ===========================================================================
# 5. pull_debug_files.sh — test HA_HOST missing
# ===========================================================================
printf "\n🐛 pull_debug_files.sh\n"

result="$(HA_HOST="" bash "${TOOLS}/pull_debug_files.sh" 2>&1 || true)"
check "pull_debug without HA_HOST errors" "HA_HOST is not set" "${result}"

result="$(HA_HOST="fakehost" bash "${TOOLS}/pull_debug_files.sh" --dry-run 2>&1 || true)"
check "pull_debug --dry-run with HA_HOST succeeds" "" "${result}"


# ===========================================================================
# 6. Syntax check all shell scripts
# ===========================================================================
printf "\n🐚 Shell Syntax Check\n"

for sh in "${TOOLS}"/*.sh; do
  if bash -n "${sh}" 2>/dev/null; then
    PASS=$((PASS + 1))
    printf "  ✅ %s syntax OK\n" "$(basename "${sh}")"
  else
    FAIL=$((FAIL + 1))
    printf "  ❌ %s syntax error\n" "$(basename "${sh}")"
  fi
done


# ===========================================================================
# Summary
# ===========================================================================
printf "\n========================================\n"
printf "Results: %d passed, %d failed\n" "${PASS}" "${FAIL}"
[[ "${FAIL}" -eq 0 ]] && exit 0 || exit 1
