# LLM Integration Setup (Ollama & OpenCode)

This guide explains how to connect Home Assistant to AI models for dynamic text generation (like personalized TTS announcements, weather summaries, or dynamic jokes).

The template supports switching between two providers using a dashboard dropdown helper (`input_select.ai_provider_selector`):
1. **Local (Ollama)** — Runs on your own hardware, free, secure, but requires a good GPU/CPU.
2. **Cloud (OpenCode)** — Connects to a cloud AI endpoint via the OpenCode proxy.

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

Create `/etc/opencode/env` with your secrets:
```ini
OPENCODE_SERVER_PASSWORD=txxxx
OPENCODE_API_KEY=sk-xxxxx
```

Secure the environment file:
```bash
sudo chown root:root /etc/opencode/env
sudo chmod 600 /etc/opencode/env
```

Enable and start the service:
```bash
systemctl --user enable opencode-server
systemctl --user start opencode-server
systemctl --user status opencode-server
```

> **Note:** The `--hostname 127.0.0.1` flag restricts access to the local machine. If Home Assistant is on a different host, keep OpenCode bound to loopback and expose it through a TLS-authenticated reverse proxy or tunnel. Then set `<OPENCODE_IP>` to the proxy's reachable address in the REST commands below, ensuring `opencode_authorization` is not sent in plaintext.

### 2. Home Assistant REST Command
Add this to your `configuration.yaml`.

```yaml
rest_command:
  opencode_create_session:
    url: "https://<OPENCODE_IP>:4096/session"
    method: POST
    timeout: 30
    headers:
      Content-Type: "application/json"
      Authorization: !secret opencode_authorization
    payload: "{}"
  
  opencode_post_message:
    url: "https://<OPENCODE_IP>:4096/session/{{ session_id }}/message"
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
    url: "http://<OPENCODE_IP>:4096/health"
    method: GET
    timeout: 10
    headers:
      Authorization: !secret opencode_authorization

  ghostfolio_api_get_performance:
    url: "http://<GHOSTFOLIO_IP>:3333/api/performance/<your_ghostfolio_portfolio_id>"
    method: GET
    timeout: 30
    headers:
      Authorization: !secret ghostfolio_authorization
```

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
