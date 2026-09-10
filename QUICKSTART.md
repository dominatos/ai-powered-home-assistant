# Quick Start

Get up and running in 5 minutes using a **private Git repository** — the recommended way to manage your Home Assistant configuration with AI.

## Why Private Git?

- **Version control** — every AI change is tracked with full history
- **Rollback** — undo any mistake with `git revert`
- **Sync between PC and HA** — commit on PC, pull on HAOS
- **Safety net** — clean git tree required before any sync operation

**The workflow:** Clone the template → rename the files → document your house → pull your HA config into the repo → use AI to generate automations → deploy back to HA.

## Prerequisites

- Python 3.10+
- Git
- An AI IDE (see [README.md](README.md#4-setup-ai-ai-ide) for options)
- Home Assistant instance (local or remote)
- A **private** GitHub/GitLab/Bitbucket account

## Step 1: Create Your Private Repo

1. Create a **new private repository** on GitHub/GitLab/Bitbucket
2. Clone this template and push it as your own:

**Option A: One command (recommended)**

Download and run the setup script — it clones, renames, and pushes for you:
```bash
bash <(curl -s https://raw.githubusercontent.com/dominatos/ai-powered-home-assistant/main/tools/install-private-repo.sh) git@github.com:<your-username>/<your-private-repo>.git
```

**Option B: Manual steps**

```bash
# Clone the template repository
git clone https://github.com/dominatos/ai-powered-home-assistant.git
cd ai-powered-home-assistant

# Replace the template remote with your own repo
# (two separate commands — remove the old, then add yours)
git remote remove origin
git remote add origin https://github.com/<your-username>/<your-private-repo>.git

# Rename all template files (preserving canonical casing)
# This strips ".template." from every filename so you get working copies:
#   automations-basic.template.yaml → automations-basic.yaml
# Special case: AUTOMATIONS_KB.template.md → automations_kb.md (lowercase)
for f in *.template.*; do
  if [ "$f" = "AUTOMATIONS_KB.template.md" ]; then
    mv "$f" "automations_kb.md"
  else
    mv "$f" "${f//.template./.}"
  fi
done

# Commit the initial state
git add .
git commit -m "Initial setup with renamed templates"
git push --set-upstream origin main --force
```

This creates your working copies:
- `HOUSE_CONTEXT.md`
- `automations-basic.yaml`
- `automations-advanced.yaml`
- `dashboard-basic.yaml`
- `dashboard-advanced.yaml`

**Important:** Replace the `<your-name>` placeholder in the `LICENSE` file with your actual name before publishing.

> **You need the same repo on two machines:** your personal PC (where you use the AI) and your Home Assistant server (where the config lives). After pushing from your PC, clone the same repo on HAOS — see [Step 6: Deploy Changes](#step-6-deploy-changes) for the HAOS setup.

## Step 2: Document Your House

Open `HOUSE_CONTEXT.md` and fill in:
1. Your rooms and their layout
2. Which rooms connect to which
3. All your devices (sensors, lights, switches, etc.)

**Tip:** If you have many devices already in HA, paste `prompts/HC-gen.md` into your AI IDE to auto-generate this file from your inventory.

```bash
git add HOUSE_CONTEXT.md
git commit -m "Document house layout and devices"
git push
```

## Step 3: Configure the Prompt

Open `prompts/prompt.txt` and update the `Repository root:` path so the AI knows where your files are:
```text
Repository root: /path/to/your/ai-powered-home-assistant
```

## Step 4: Pull Your HA Config

> **Requires a running Home Assistant instance** with the SSH/Samba add-on or API access. If you're just testing locally without HA, skip this step — your templates will still work, just without real device data.

These scripts connect to your running Home Assistant instance and pull its config into the repo:

```bash
# First time: export your device inventory (creates ha_device_inventory.json)
./tools/export_ha_inventory.sh

# Then sync your automations, scripts, scenes
./tools/sync_from_homeassistant.sh

# Push the synced config (the script already committed automatically)
git push --set-upstream origin main
```

This pulls your actual `automations.yaml`, `scripts.yaml`, etc. into the repo so the AI has real context.

> **Not on HAOS?** The scripts default to `/homeassistant`. If your HA config is elsewhere, set `SOURCE_ROOT`:
> ```bash
> SOURCE_ROOT=/path/to/your/ha/config ./tools/sync_from_homeassistant.sh
> ```

## Step 5: Start Using AI

1. Open the repo folder in your AI IDE
2. Open the AI chat panel
3. Paste the contents of `prompts/prompt.txt`
4. Fill in the `[INSERT_YOUR_CURRENT_TASK_HERE]` section
5. Let the AI work — it will read your files and generate automations

## Step 6: Deploy Changes

After the AI generates something you like:

```bash
# Review what changed
git diff

# Commit the AI changes
git add .
git commit -m "Add bathroom motion automation"
git push

# On HAOS: pull the changes
git pull

# Push to Home Assistant
TARGET_ROOT=/config ./tools/sync_to_homeassistant.sh
```

## Syncing Between PC and HAOS

### Option A: SSH/Samba (Simple)

1. Enable **Samba Share** or **SSH & Web Terminal** add-on in HAOS
2. Mount `/config` folder, or use `sync_from_homeassistant.sh` via SSH/SCP
3. Sync scripts handle the rest

### Option B: Git (Recommended)

```bash
# On HAOS (first time only)
cd /config
git clone https://github.com/<your-username>/<your-private-repo>.git ai-home-assistant
cd ai-home-assistant
git config user.email "ha@home.local"
git config user.name "Home Assistant"
```

```bash
# On HAOS (daily workflow)
cd /config/ai-home-assistant
git pull
TARGET_ROOT=/config ./tools/sync_to_homeassistant.sh
```

This gives you a clean, auditable history of every change.

## Safety First

- Every sync creates backups in `.sync_backups/`
- Use `--dry-run` to preview changes: `./tools/sync_to_homeassistant.sh --dry-run`
- Use `--diff` to see what's different: `./tools/sync_to_homeassistant.sh --diff`
- Scripts require a clean git tree before running
- Never commit `secrets.yaml` or `.storage/` (`.gitignore` handles this)

## Next Steps

- Read the full [README.md](README.md) for advanced features
- Explore [prompt templates](prompts/) for specific tasks
- Check [patterns/standardize.md](patterns/standardize.md) for reusable automation logic
- Set up [CodeRabbit](README.md#-code-review-coderabbit) for automated PR reviews

### Advanced / Optional Reference Docs
- [FUTURE-automations.template.md](FUTURE-automations.template.md) — design complex automations before implementing
- [heating.template.md](heating.template.md) — thermostat schedule architecture & automation interaction matrix
- [README-ollama.template.md](README-ollama.template.md) — local AI (Ollama) integration with HA
- [sell-mode-plan.template.md](sell-mode-plan.template.md) — runtime sell-mode pattern for disabling personal automations
- [remove-customization.template.md](remove-customization.template.md) — handover checklist
- [configuration.template.yaml](configuration.template.yaml) — common `configuration.yaml` patterns
- [scripts.template.yaml](scripts.template.yaml) — example reusable scripts
- [scenes.template.yaml](scenes.template.yaml) — example scenes
