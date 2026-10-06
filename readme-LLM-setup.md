# LLM Integration Setup (Ollama & OpenCode)

This guide explains how to connect Home Assistant to AI models for dynamic text generation (like personalized TTS announcements, weather summaries, or dynamic jokes).

The template supports switching between two providers using a dashboard dropdown helper (`input_select.ai_provider_selector`):
1. **Local (Ollama)** — Runs on your own hardware, free, secure, but requires a good GPU/CPU.
2. **Cloud (OpenCode)** — Runs an [OpenCode Server](https://opencode.ai/docs/server) bridge that HA calls over HTTPS via a TLS reverse proxy.

**Example deployment notes** (roles, binds, and endpoints) are in [§7](#7-production-notes-example).

---

## 1. Setting Up Local AI (Ollama)

Ollama allows you to run models like Qwen, Llama, or Gemma locally.

### Prerequisites
- A machine running [Ollama](https://ollama.com/) on your local network (e.g., `192.168.X.Y:11434`).
- For Home Assistant TTS, we recommend creating a custom model that is instructed **never to output reasoning or thinking**, as TTS engines will read the reasoning out loud.

### Creating a "No-Think" Custom Model
1. Open a terminal on a machine that can reach your Ollama server.
2. Pull a base model (e.g., `qwen2.5-vl:7b`):
   ```bash
   curl -s http://<OLLAMA_IP>:11434/api/pull -d '{"name": "qwen2.5-vl:7b"}'
   ```
3. Create the custom model with a strict system prompt:
   ```bash
   curl -s -X POST http://<OLLAMA_IP>:11434/api/create \
     -H "Content-Type: application/json" \
     -d '{
       "model": "qwen2.5-vl-nothink",
       "from": "qwen2.5-vl:7b",
       "system": "You are a concise multimodal assistant.\n\nAlways answer directly.\nNever output reasoning or thinking.\nNever explain your thought process.\nRespond only with the final answer.",
       "params": {
         "temperature": 0.6,
         "top_p": 0.95,
         "repeat_penalty": 1.0,
         "num_predict": 256
       }
     }'
   ```

### Home Assistant REST Command
Add this to your `configuration.yaml`:

```yaml
rest_command:
  ollama_generate_joke:
    url: "http://<OLLAMA_IP>:11434/api/generate"
    method: POST
    timeout: 60
    headers:
      Content-Type: "application/json"
    payload: >
      {
        "model": "qwen2.5-vl-nothink",
        "prompt": {{ prompt | to_json }},
        "stream": false,
        "options": {
          "num_predict": 500,
          "temperature": 0.9
        }
      }
```

---

## 2. Setting Up Cloud AI (OpenAI-Compatible API)

If you prefer using a cloud provider (like OpenAI, Groq, or Anthropic via an OpenAI wrapper), you can set up a second REST command.

### Home Assistant REST Command
Add this to your `configuration.yaml`. (Make sure to add `cloud_api_authorization: "Bearer sk-..."` to your `secrets.yaml` file).

```yaml
rest_command:
  cloud_generate:
    url: "https://api.openai.com/v1/chat/completions" # Replace with your provider's URL
    method: POST
    timeout: 60
    headers:
      Content-Type: "application/json"
      Authorization: !secret cloud_api_authorization
    payload: >
      {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": {{ prompt | to_json }}}],
        "max_tokens": 500,
        "temperature": 0.9
      }
```

---

## 3. Setting Up OpenCode Server

If you use the [OpenCode Server](https://opencode.ai/docs/server) as a bridge, you can run it via a systemd user service.

### 1. Systemd Service Setup
Create the service at `~/.config/systemd/user/opencode-server.service`:

**Local tools only** (HA on another machine — do **not** use this for HA Cloud):

```ini
[Unit]
Description=OpenCode Server (port 4096)
After=network.target

[Service]
Type=simple
EnvironmentFile=/etc/opencode/env
ExecStart=/home/YOUR_USER/.opencode/bin/opencode serve --hostname 127.0.0.1 --port 4096
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

**HA-reachable on a trusted LAN** (Home Assistant on a different host):

```ini
ExecStart=/home/YOUR_USER/.opencode/bin/opencode serve --hostname 0.0.0.0 --port 4096
```

| Bind | Use when |
|------|----------|
| `127.0.0.1` | Scripts/agents on the **same** machine only |
| loopback + TLS reverse proxy | HA (or other LAN clients) must call this host — terminate TLS at the proxy; HA rest_commands send Basic Auth over HTTPS |
| `0.0.0.0` | Raw service bind on a trusted LAN only; still front with a TLS reverse proxy before HA authenticates |

Create `/etc/opencode/env` with your secrets:
```ini
OPENCODE_SERVER_PASSWORD=txxxx
OPENCODE_API_KEY=sk-xxxxx
```

Secure the environment file (the systemd **user** service runs as `YOUR_USER`
and cannot read a root-owned mode-600 file):
```bash
sudo chown YOUR_USER:YOUR_USER /etc/opencode/env
sudo chmod 600 /etc/opencode/env
```

Enable and start the service:
```bash
systemctl --user enable opencode-server
systemctl --user start opencode-server
systemctl --user status opencode-server
```

### 2. Linger — required for HA-reachable servers

OpenCode runs as a **systemd user** service. If linger is off, the user
manager (and therefore `opencode-server`) stops when your last SSH session
ends. Home Assistant then logs:

```text
Cannot connect to https://<your_opencode_reverse_proxy_host>/global/health
```

This was the root cause of the 2026-10-05 health-check outage.

```bash
loginctl enable-linger YOUR_USER
loginctl show-user YOUR_USER | grep Linger   # expect: Linger=yes
```

**Verify:** log out, wait ~60s, log in again — service must still be `active (running)`.

### 3. Do not restart this unit on a short cron

**Do not** add crontab entries such as:

```bash
0 * * * * /usr/bin/systemctl --user restart opencode-server.service
```

That creates a brief outage every hour (and HA health checks that fire
near :00 can fail even when the rest of the hour is fine). Use
`Restart=on-failure` for crashes and linger for logout survival.

### 4. Health endpoint

Live OpenCode Server health path is:

```http
GET /global/health
Authorization: Basic base64(opencode:<OPENCODE_SERVER_PASSWORD>)
```

Example success body:

```json
{"healthy": true, "version": "1.18.34"}
```

Older notes sometimes used `/health`. Confirm the path on your build
(`GET /doc` OpenAPI spec, or a curl test) before hardcoding it in HA.

### 5. Home Assistant REST Command
Add this to your `configuration.yaml`.

```yaml
rest_command:
  opencode_create_session:
    url: "https://<your_opencode_reverse_proxy_host>/session"
    method: POST
    timeout: 30
    headers:
      Content-Type: "application/json"
      Authorization: !secret opencode_authorization
    payload: "{}"

  opencode_post_message:
    url: "https://<your_opencode_reverse_proxy_host>/session/{{ session_id }}/message"
    method: POST
    timeout: 60
    headers:
      Content-Type: "application/json"
      Authorization: !secret opencode_authorization
    payload: >
      {
        "parts": [{"type": "text", "text": {{ prompt | to_json }}}]
      }

  opencode_health_check:
    url: "https://<your_opencode_reverse_proxy_host>/global/health"
    method: GET
    timeout: 10
    headers:
      Authorization: !secret opencode_authorization
```

Basic Auth username: `opencode`. Store the Authorization header value in
`secrets.yaml` as `opencode_authorization` (matching the `!secret
opencode_authorization` references above). These URLs send the Basic Auth
secret, so they **must** use `https://` (terminate TLS at a reverse proxy in
front of OpenCode; do not send Basic Auth over plaintext HTTP).

```yaml
  ghostfolio_api_get_performance:
    url: "https://<your_ghostfolio_reverse_proxy_host>/api/performance/<your_ghostfolio_portfolio_id>"
    method: GET
    timeout: 30
    headers:
      Authorization: !secret ghostfolio_authorization
```

### 6. HA-reachable vs loopback

| Instance | Bind | Auth | Called by HA? |
|----------|------|------|----------------|
| OpenCode on HA's AI host (e.g., `YOUR_AI_HOST`) | Behind TLS reverse proxy | Basic Auth + password over HTTPS | **Yes** — Cloud (OpenCode) provider |
| OpenCode on your workstation | `127.0.0.1:4096` | Often none / local only | **No** — local coding agents only |

Do not point HA `rest_command` URLs at a workstation loopback instance.

---

## 4. Creating the Switchable Architecture

Instead of hardcoding the AI provider into every automation, use an `input_select` helper and a universal parser. This allows you to instantly switch the entire house to Cloud AI if your local server goes offline.

### 1. Add the Helper (`configuration.yaml`)
```yaml
input_select:
  ai_provider_selector:
    name: AI Provider
    options:
      - "Local (Ollama)"
      - "Cloud (OpenCode)"
    initial: "Local (Ollama)"
    icon: mdi:robot
```

### 2. Universal Automation Pattern
Use this pattern in your automations (`automations.yaml`) when you need to generate AI text:

```yaml
- variables:
    ai_prompt: "Tell me a short, sarcastic joke about the weather today."
- choose:
  - conditions:
    - condition: state
      entity_id: input_select.ai_provider_selector
      state: "Cloud (OpenCode)"
    sequence:
    - action: rest_command.opencode_create_session
      continue_on_error: true
      response_variable: session_res
    - if:
      - condition: template
        value_template: "{{ session_res is defined and session_res.status == 200 and session_res.content is defined and session_res.content.id is defined }}"
      then:
      - action: rest_command.opencode_post_message
        continue_on_error: true
        data:
          session_id: "{{ session_res.content.id }}"
          prompt: '{{ ai_prompt }}'
        response_variable: raw_ai_response
      - variables:
          ai_response:
            status: "{{ raw_ai_response.status | default(0) | int(0) }}"
            content:
              response: "{% set parts = raw_ai_response.content.parts | default([]) %}{% set texts = parts | selectattr('type', 'eq', 'text') | list %}{% if texts | length > 0 %}{{ texts[0].text }}{% endif %}"
      - action: tts.speak
        target:
          entity_id: tts.google_translate_en_com
        data:
          media_player_entity_id: media_player.living_room_speaker
          message: >
            {% if ai_response is defined and ai_response.status == 200 %}
              {% set content = ai_response.content %}
              {% if content is mapping and 'response' in content and content.response | trim | length > 0 %}
                {{ content.response | replace('*', '') | replace('"', '') }}
              {% else %}
                Failed to generate message.
              {% endif %}
            {% else %}
              Failed to generate message.
            {% endif %}
  default:
  - action: rest_command.ollama_generate_joke
    continue_on_error: true
    data:
      prompt: '{{ ai_prompt }}'
    response_variable: ai_response
  - action: tts.speak
    target:
      entity_id: tts.google_translate_en_com
    data:
      media_player_entity_id: media_player.living_room_speaker
      message: >
        {% if ai_response is defined and ai_response.status == 200 %}
          {% set content = ai_response.content %}
          {% if content is mapping and 'response' in content and content.response | trim | length > 0 %}
            {{ content.response | replace('*', '') | replace('"', '') }}
          {% elif content is mapping and 'choices' in content and content.choices | length > 0 %}
            {{ content.choices[0].message.content | replace('*', '') | replace('"', '') }}
          {% else %}
            Failed to generate message.
          {% endif %}
        {% else %}
          Failed to generate message.
        {% endif %}
```

By using this template, you build a resilient smart home that benefits from AI but gracefully falls back if services go down.

### 3. Hourly health-check automation (optional but recommended)

```yaml
- alias: "System: AI Provider Hourly Health Check"
  description: >
    Checks OpenCode API health every hour (at :30). Auto-switches to Local
    (Ollama) on failure and auto-recovers back to Cloud (OpenCode) when
    healthy. Scheduled runs are silent; notify only on manual trigger.
  trigger:
    - platform: time_pattern
      minutes: '30'
  action:
    - action: rest_command.opencode_health_check
      continue_on_error: true
      response_variable: health_response
    - variables:
        is_healthy: >-
          {{ health_response is defined
             and health_response.status == 200
             and health_response.content is defined
             and health_response.content.healthy | default(false) }}
        current_provider: "{{ states('input_select.ai_provider_selector') }}"
    - choose:
        - conditions:
            - "{{ not is_healthy and current_provider == 'Cloud (OpenCode)' }}"
          sequence:
            - action: input_select.select_option
              target:
                entity_id: input_select.ai_provider_selector
              data:
                option: "Local (Ollama)"
        - conditions:
            - "{{ is_healthy and current_provider == 'Local (Ollama)' }}"
          sequence:
            - action: input_select.select_option
              target:
                entity_id: input_select.ai_provider_selector
              data:
                option: "Cloud (OpenCode)"
  mode: single
```

---

## 5. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `Cannot connect to https://<your_opencode_reverse_proxy_host>/...` | Service down; linger off; wrong `--hostname`; firewall; proxy down | Enable linger; start unit; confirm listen address; health curl |
| Service stops when you log out of SSH | `Linger=no` | `loginctl enable-linger YOUR_USER` |
| Failures only near :00 | Hourly `systemctl --user restart` cron | Remove that crontab line |
| HTTP 401 | Basic Auth password mismatch | Align env password ↔ `secrets.yaml` |
| Health 404 | Wrong path | Use `/global/health` (confirm on your build) |
| HA can't see workstation OpenCode | Bound to `127.0.0.1` | Expected — point HA at an HA-reachable host |

```bash
systemctl --user status opencode-server
ss -lntp | grep 4096
# /etc/opencode/env is mode 600 owned by YOUR_USER (required for the user service).
# The password is expanded only inside the shell and is not printed.
# This curl targets the raw loopback service only — not the HA-facing HTTPS endpoint.
set -a; . /etc/opencode/env; set +a; curl -sS -u "opencode:${OPENCODE_SERVER_PASSWORD}" http://127.0.0.1:4096/global/health
```

---

## 6. Security notes

- Keep `OPENCODE_SERVER_PASSWORD`, `OPENCODE_API_KEY`, and HA `secrets.yaml` out of Git.
- HA-facing OpenCode URLs must use HTTPS (TLS reverse proxy); never send Basic Auth over plaintext HTTP to Home Assistant.
- Local loopback OpenCode instances are for tools on that machine, not for Home Assistant.

---

## 7. Production notes (example)

Optional deployment mapping (replace with your own hosts on your install):

| Role | Host | Endpoint |
|------|------|----------|
| Home Assistant | `<your_ha_host>` | `/homeassistant` |
| OpenCode Server (Cloud provider) | `<your_opencode_host>` | `https://<your_opencode_reverse_proxy_host>` |
| Ollama (Local fallback) | `<your_ollama_host>` | `http://<your_ollama_host>:11434/api/generate` |
| OpenCode on local workstation | `<your_workstation>` | `127.0.0.1:4096` only — **not** used by HA |

Live unit example: `--hostname 0.0.0.0 --port 4096`, `EnvironmentFile=/etc/opencode/env`, linger **yes**, no restart cron, health `/global/health`.

HA secrets example: `opencode_authorization` = Basic Auth header for user `opencode`.
