# AI-Powered Home Assistant

This repository is a framework and template for managing your Home Assistant instance using an LLM (like Claude, ChatGPT, or Gemini) as your personal Senior Home Assistant Engineer.

Many people use AI to generate simple Home Assistant YAML scripts, but they quickly run into problems: the AI hallucinates entity IDs, breaks existing automations, or misunderstands how the physical house is laid out (e.g., turning off the bathroom light while someone is in the shower).

This repository solves that problem by providing a **strict context and tooling framework**.

**Recommended workflow:** Use a **private Git repository** on GitHub/GitLab/Bitbucket to sync changes between your PC and Home Assistant. This gives you version control, rollback capability, and a safety net for all AI-generated changes. See [Quick Start Guide](QUICKSTART.md) or [Git Syncing](#6-git-syncing-recommended) below.

## Getting Started

### 1. Clone this Template
Clone or download this repository to your computer (preferably to a local workspace, not directly into your production `/homeassistant` folder).

**Quick setup (one command):**
```bash
bash <(curl -s https://raw.githubusercontent.com/dominatos/ai-powered-home-assistant/main/tools/install-private-repo.sh) git@github.com:<your-username>/<your-private-repo>.git
```
This clones the template, renames all `.template.*` files, and pushes to your private repo.
The target repository must be **empty** — the script refuses to overwrite an existing history unless you pass `--force`. See [QUICKSTART.md](QUICKSTART.md) for the manual steps.

> **Next: clone your private repo on your personal PC.** If you used the curl command above, it already cloned and pushed for you. If you set up the repo manually on another machine, clone it on your PC now:
> ```bash
> git clone git@github.com:<your-username>/<your-private-repo>.git
> ```
> You'll work from this clone on your PC. The same repo also needs to live on your HAOS server — see [Step 5: Connecting to HAOS](#5-connecting-to-haos) and [Step 6: Git Syncing](#6-git-syncing-recommended).

### 2. Set Up Your Context
1. Rename all `.template.*` files by removing only the `.template` segment while preserving canonical casing, with one exception: `AUTOMATIONS_KB.template.md` → `automations_kb.md` (e.g., `HOUSE_CONTEXT.template.md` → `HOUSE_CONTEXT.md`, `dashboard.template.yaml` → `dashboard.yaml`, `automations-basic.template.yaml` → `automations-basic.yaml`).
2. Open `HOUSE_CONTEXT.md` and document your physical house layout, rooms, and devices. Be as descriptive as possible. *(Tip: If you already have a lot of devices and automations in Home Assistant, you can paste the contents of `prompts/HC-gen.md` into the AI IDE to have it automatically generate your `HOUSE_CONTEXT.md` for you!)*
3. Open `prompts/prompt.txt` and read the prompt structure. Update the `Repository root:` path to match your local setup.

### 3. Sync Your Configuration (`tools/` folder)

This repository includes several scripts in the `tools/` folder to safely move files between your live Home Assistant server and this local repository. 

*Note: These scripts default to `/homeassistant` as the Home Assistant directory. If your setup differs (e.g., you use `/config` on HAOS), you can override the paths using environment variables like `SOURCE_ROOT` and `TARGET_ROOT`.*

**Available Scripts:**

- **`tools/sync_from_homeassistant.sh`**
  Pulls the latest automations, scripts, scenes, and configurations from your live Home Assistant server into this repository. Run this *before* you start working with the AI to ensure the AI has the most up-to-date context. 
  *Usage:* `./tools/sync_from_homeassistant.sh` (Supports `--dry-run` and `--diff`)

- **`tools/sync_to_homeassistant.sh`**
  Pushes the generated and modified configuration files from this repository back to your live Home Assistant server. Run this *after* the AI has finished its work and you have reviewed the changes.
  *Usage:* `./tools/sync_to_homeassistant.sh` (Supports `--dry-run` and `--diff`)

- **`tools/export_ha_inventory.sh`**
  Reads the hidden `.storage` folder in Home Assistant and exports a clean, sanitized list of all your devices and entities into `ha_device_inventory.json` and `inventory.txt`. This gives the AI exact entity IDs so it never has to guess. (The `sync_from_homeassistant.sh` script usually runs this automatically).
  *Usage:* `./tools/export_ha_inventory.sh` (Uses `STORAGE_DIR` environment variable)

**Safety Features:**
Both sync scripts automatically create backups in a `.sync_backups/` folder before making any changes. If something goes wrong, you can easily run the `restore.sh` script found in the backup folder to revert the changes. They also require your Git working tree to be clean before running, ensuring you can undo any mistakes via Git.

### 4. Setup AI IDE
For the best experience, do not use simple web chats (like ChatGPT). Instead, use an agentic AI IDE or coding agent installed on your personal PC.

#### Dedicated AI IDEs

| IDE | Description | Link |
|-----|-------------|------|
| **Google Antigravity** | Google's agentic development platform with IDE, CLI, SDK, and multi-agent support | [antigravity.google/product/antigravity-ide](https://antigravity.google/product/antigravity-ide) |
| **Cursor** | AI-powered code editor with agents, cloud automation, and multi-model support | [cursor.com](https://cursor.com) |
| **Devin Desktop** | Multi-agent command center with built-in IDE (formerly Windsurf) | [devin.ai](https://devin.ai) |
| **Zed** | Fast, collaborative code editor with built-in AI assistance | [zed.dev](https://zed.dev) |

#### CLI Coding Agents

| Tool | Description | Link |
|------|-------------|------|
| **OpenCode** | Open source AI coding agent for terminal, desktop, and IDE extensions | [opencode.ai](https://opencode.ai) |
| **Claude Code** | Anthropic's agentic CLI — terminal, VS Code, JetBrains, desktop, web | [claude.ai/code](https://claude.ai/code) |
| **Codex** | OpenAI's lightweight coding agent for terminal, with IDE extensions and desktop app | [github.com/openai/codex](https://github.com/openai/codex) |
| **Aider** | AI pair programming in your terminal with git integration | [aider.chat](https://aider.chat) |

#### VS Code / JetBrains Extensions

| Extension | Description | Link |
|-----------|-------------|------|
| **GitHub Copilot** | AI pair programmer with chat, code completion, and agent mode | [github.com/features/copilot](https://github.com/features/copilot) |
| **Cline** | Open source autonomous coding agent (VS Code, JetBrains, CLI, SDK) | [cline.bot](https://cline.bot) |

#### Utilities

| Tool | Description | Link |
|------|-------------|------|
| **OmniRoute** | Free AI gateway — hundreds of providers, auto-fallback, token compression. Point any coding agent at one endpoint | [omniroute.online](https://omniroute.online) |

#### How to Use

1. Open this repository folder in your AI IDE.
2. The AI will automatically have access to all your files (`automations.yaml`, `HOUSE_CONTEXT.md`, etc.).
3. When you are ready to build a complex automation, open the AI chat panel inside the IDE.
4. Paste the contents of `prompts/prompt.txt`, ensuring you fill out the `[INSERT_YOUR_CURRENT_TASK_HERE]` block.
5. The AI IDE will read your files, write the new automations, and even execute the sync tools for you!

### 5. Connecting to HAOS
If your Home Assistant is running on a dedicated device like a Raspberry Pi or Mini PC (HAOS), you should keep this repository on your personal PC and use the network to sync:
1. Enable the **Samba Share** or **SSH & Web Terminal** Add-on in Home Assistant OS.
2. Mount the Home Assistant `/config` folder to your PC, or configure the `tools/sync_from_homeassistant.sh` script to pull files via SSH/SCP.
3. The AI IDE runs entirely on your PC, safely modifying the files in this local repository. Once the AI finishes writing an automation and you approve it, use the sync tools to push the updated `automations.yaml` back to HAOS.

### 6. Git Syncing (Recommended)

**This is the preferred way to manage your configuration.** A private Git repository gives you version control, rollback capability, and a safety net for all AI-generated changes.

First, set up the base template on HAOS (via SSH/Terminal):
```bash
cd /config
git clone https://github.com/YOUR_USERNAME/ai-powered-home-assistant/
cd ai-powered-home-assistant

# Rename template files to working filenames
for f in *.template.*; do
  if [ "$f" = "AUTOMATIONS_KB.template.md" ]; then
    mv "$f" "automations_kb.md"
  else
    mv "$f" "${f//.template./.}"
  fi
done

rm -rf .git
```

Next, create a private repository to sync with your PC:
1. Create a **New Repository** on GitHub, GitLab, or Bitbucket. Make sure to set its visibility to **Private**.
2. Initialize your local Git repository on HAOS and push it to your new remote:
   ```bash
   git init
   git add .
   git commit -m "Initial config"
   git branch -M main
   git remote add origin <your-private-repo-url>
   git push -u origin main
   ```
3. **On your PC**, clone your new *private* repository and open it in your AI IDE.
4. As the AI generates and modifies files on your PC, you can commit and push them. Then, simply run `git pull` on HAOS to deploy the updates and launch `tools/sync_to_homeassistant.sh` to push the changes.

**Workflow:**
```text
PC (AI IDE) → git push → Private Repo → git pull → HAOS → sync_to_homeassistant.sh → Home Assistant
```

This gives you a clean, auditable history of every change and makes it easy to undo mistakes with `git revert`.

## What's Included

### 🛠️ Sync & Export Scripts (`tools/`)
Shell scripts to safely move files between your live Home Assistant and this repository:

| Script | Purpose |
|--------|---------|
| `tools/sync_from_homeassistant.sh` | Pull latest config from HA → repo (run *before* AI work) |
| `tools/sync_to_homeassistant.sh` | Push AI-generated changes repo → HA (run *after* review) |
| `tools/export_ha_inventory.sh` | Export all device/entity IDs so the AI never guesses |
| `tools/check_docs.py` | Validates that every automation is documented in `HOUSE_CONTEXT.md` |
| `tools/dashboard_audit.py` | Validates entity references in `dashboard.yaml` against the inventory |
| `tools/pull_debug_files.sh` | Securely pulls logs and traces from a remote HA instance |
| `tools/backup_automations.py` | Creates point-in-time YAML backups of specific automations |

The sync scripts create automatic backups (where applicable), support `--dry-run` and `--diff` flags, and require a clean Git tree for safety. See [Sync Your Configuration](#3-sync-your-configuration-tools-folder) below for details.

- **`tools/test_all.py`** — Validates all templates, tools, and documentation in one run:
  ```bash
  python3 tools/test_all.py
  ```

### 🔍 Code Review (CodeRabbit)

This repository includes a [CodeRabbit](https://coderabbit.ai) configuration for automated AI code reviews on pull requests. To enable it:

1. Install the [CodeRabbit GitHub App](https://github.com/apps/coderabbit) on your repository
2. The `.coderabbit.yaml` config is already set up with path-specific review rules for:
   - Template files — checks for personal data and placeholder consistency
   - Python tools — validates error handling and documentation
   - Shell scripts — enforces safety patterns (`set -Eeuo pipefail`, backups)
   - Tests — ensures proper temp directory cleanup

#### Utility Scripts

Helper scripts for less common tasks:

| Script | Purpose |
|--------|---------|
| `tools/generate_automations_kb.py` | Regenerates `automations_kb.md` from `automations.yaml` |
| `tools/export_ha_inventory.py` | Python implementation of inventory export |
| `tools/sync_common.sh` | Shared library sourced by sync scripts (internal) |
| `tools/generate_yaml_template.py` | Generates YAML templates from Python data structures |
| `tools/write_yaml_template.py` | Writes large YAML files exceeding opencode's payload limit |

### 🤖 Ready-to-Use AI Prompts (`prompts/`)
Drop-in prompt templates you paste into your AI IDE to perform specific tasks:

| Prompt | What It Does |
|--------|-------------|
| `prompts/prompt.txt` | **Main session prompt** — the starting point for any AI task |
| `prompts/dashboard--current.md` | **Dashboard edit prompt** — starting point for modifying Lovelace dashboards |
| `prompts/HC-gen.md` | Auto-generate `HOUSE_CONTEXT.md` from your existing inventory |
| `prompts/naming-fix.md` | Standardize all automation names to `Room: Action` format |
| `prompts/energy-saving.md` | Audit for energy waste (vampire drain, missing timeouts) |
| `prompts/security-audit.md` | Find security flaws and missing fallbacks in your automations |
| `prompts/dashboard-gen.md` | Auto-generate a Lovelace dashboard from your house context |
| `prompts/yaml-cleanup.md` | Modernize YAML syntax without changing behavior |
| `prompts/optimise.md` | Merge redundant automations and improve robustness |
| `prompts/invent-new.md` | Brainstorm brand new automations based on your devices |
| `prompts/describe-idea.md` | Architect your idea into a detailed plan in `FUTURE-automations.md` |
| `prompts/replace-device.md` | Swap old entity IDs for new ones across all files |
| `prompts/troubleshoot-trace.md` | Paste a JSON trace or error log and get a plain-English diagnosis |

### 📋 Context & Rules
| File | Purpose |
|------|---------|
| `INSTRUCTIONS.md` | Strict rules that prevent the AI from guessing or breaking things |
| `HOUSE_CONTEXT.template.md` | Template to describe your physical house layout and devices |
| `AUTOMATIONS_KB.template.md` | Template for the human-readable summary of all automations |
| `automations-basic.template.yaml` | Simple automations: motion lighting, safety sensors, thermostat, A/C sync |
| `automations-advanced.template.yaml` | AI-powered automations: Ollama/OpenCode weather, calendar, A/C advisor |
| `dashboard-basic.template.yaml` | Basic Lovelace views: Overview, Kitchen, Bedroom, Bathroom, Child Room |
| `dashboard-advanced.template.yaml` | Advanced views: Climate, Energy, Appliances, TV Remote, Tablet, Car |
| `automations.template.yaml` | Legacy combined automations file (superseded by basic/advanced split) |
| `dashboard.template.yaml` | Legacy combined dashboard file (superseded by basic/advanced split) |
| `patterns/standardize.md` | Canonical library of safe, reusable automation logic patterns |
| `readme-LLM-setup.md` | Guide on setting up local/cloud AI (Ollama/OpenCode) for TTS |
| `to-implement-after.template.md`| Backlog template for future automation ideas |
| `to-improve.template.md` | Backlog template for structural and architectural improvements |
| `to-assign.template.md` | Backlog template for tracking unassigned/global entities |

### 📚 Advanced & Optional Reference Docs
Reference documents for more complex setups:

| File | Purpose |
|------|---------|
| `configuration.template.yaml` | Common `configuration.yaml` patterns: helpers, recorder, templates, Ollama, Powercalc |
| `scripts.template.yaml` | Example reusable scripts: all-lights-off, TV timer, media transfer, thermostat pull |
| `scenes.template.yaml` | Example scenes: A/C cooling, evening relax, movie mode |
| `FUTURE-automations.template.md` | Design-first template for planning complex automations before implementing them |
| `heating.template.md` | Complete thermostat integration reference: schedule helpers, automations, interaction matrix |
| `README-ollama.template.md` | Local AI integration guide: Ollama setup, custom model, HA `rest_command`, troubleshooting |
| `sell-mode-plan.template.md` | Pattern for a runtime "sell mode" that disables personalized automations at the flip of a switch |
| `remove-customization.template.md` | Checklist for preparing a smart home for handover or sale — what to remove and why |

## How It Works

Instead of just asking the AI to "write an automation," you provide it with this entire repository (or parts of it) so the AI understands:
1. **Your Strict Rules:** (`INSTRUCTIONS.md`) Forces the AI to ask for permission before deleting things, validates changes against other automations, and prevents it from rewriting your entire configuration file.
2. **Your Physical House:** (`HOUSE_CONTEXT.template.md`) Gives the AI "eyes" into the real world. It knows which room connects to which, and what sensors are actually present.
3. **Your Current Automations:** You sync your actual YAML files here so the AI can analyze how a new automation might conflict with an old one.

## Example Use Cases (What to ask the AI)

Once your context is set up and your files are synced, you can ask your AI IDE to perform complex tasks safely. Here are a few examples of what you can paste into the `[INSERT_YOUR_CURRENT_TASK_HERE]` section of `prompts/prompt.txt`:

### 1. Creating a New Smart Automation
> "I bought a new Zigbee motion sensor and a smart bulb for the bathroom. I've added them to `HOUSE_CONTEXT.md`. Please write an automation that turns on the bathroom light when motion is detected, but only if the illuminance is below 50 lux. Also, make sure it turns off after 5 minutes of no motion, but DO NOT turn it off if the shower humidity sensor indicates someone is taking a shower."

### 2. Debugging Conflicting Rules
> "My living room lights keep turning off randomly while we are watching TV. Please review the automations related to the Living Room in `automations.yaml`. Identify any conflicting rules or motion sensor timeouts, explain the issue, and propose a fix that keeps the lights on if the TV (media_player.living_room_tv) is playing."

### 3. Context Updates & Scaffolding
> "I just added 5 new smart plugs around the house for holiday lights. Here is a rough list of where I put them and what they are called in Home Assistant. Please update `HOUSE_CONTEXT.md` to include these new devices in their respective rooms, and then write a script to turn them all on at sunset and off at midnight."

### 4. Analyzing Blast Radius
> "I want to change the 'Goodnight' script to also lock the front door and arm the alarm. Before doing this, please analyze all other automations that call the 'Goodnight' script. Will this change cause issues if someone runs it while someone else is still in the backyard?"

### 5. Using Utility Prompts
This repository ships with 13 ready-to-use prompt templates in the `prompts/` folder. See the full list in the [What's Included](#whats-included) section above. Simply copy the contents of any prompt file, paste it into your AI IDE chat, and fill in the placeholders.

## The Rules Engine (`INSTRUCTIONS.md`)
The `INSTRUCTIONS.md` file is the secret sauce. It forces the AI to:
- **Never guess:** If a device is missing from the context, it must stop and ask you.
- **Design for resilience:** It forces the AI to consider "off" logic as much as "on" logic (e.g., what happens if the motion sensor never triggers again?).
- **Respect the blast radius:** It forbids the AI from refactoring or "cleaning up" files unless explicitly requested.

## Security Warning
> ⚠️ **DO NOT UPLOAD YOUR SECRETS!**
> If you upload your version of this repository to GitHub, ensure that `.gitignore` is properly configured. **Never commit `secrets.yaml`, `.storage/`, or files containing MQTT passwords (like `zigbee2mqtt/configuration.yaml`) to a public repository.**

This repository includes a **Gitleaks** CI workflow (`.github/workflows/gitleaks.yml`) that scans pushes to the main/master branch and pull requests targeting those branches for leaked secrets. If a secret is detected, the CI check will fail.

## Enjoy!
Using this framework, you can build incredibly complex, intelligent automations that go far beyond the limitations of simple "If this, then that" apps like Tuya Smart, without breaking your live home environment.
