# NFS Music Library + Music Assistant + Playlist Generator

This guide explains how to set up a local audio library on an NFS share, serve it through Home Assistant's Music Assistant integration, and keep an M3U playlist automatically in sync using `python_scripts/create_playlist.py`.

## What It Does

```
NFS Server (your NAS / Linux box)
  └─ /export/music/          ← audio files live here
       │
       ├─ NFS mount on HA host at /media/music
       │
       ├─ create_playlist.py scans the folder → writes playlist.m3u
       │
       └─ Music Assistant reads playlist.m3u via Filesystem provider
            └─ Speakers play from the playlist
```

- **NFS share** holds your audio files (MP3, FLAC, WAV, AAC, OGG, M4A, WMA, OPUS).
- **`create_playlist.py`** scans the folder and generates a valid `#EXTM3U` playlist file.
- **Music Assistant** picks up the M3U via its Filesystem (NFS) provider and makes it available for playback on any speaker.
- An optional **automation** re-generates the playlist on a schedule so new files appear without manual intervention.

## Prerequisites

| Component | Requirement |
|-----------|-------------|
| NFS server | A NAS or Linux machine sharing an audio folder (e.g., `/export/music`) |
| Home Assistant | `shell_command` must be enabled in `configuration.yaml` |
| Music Assistant | Music Assistant server installed as a Home Assistant add-on/app or as a standalone Docker container (see Step 2B); the Home Assistant Music Assistant integration is separately required for the automation actions in Step 8 |
| NFS client | HA host must be able to mount NFS shares (HAOS has built-in NFS support) |

## Step 1 — Export the NFS Share

On your NFS server (example: Ubuntu/Debian):

```bash
# Install NFS server
sudo apt install nfs-kernel-server

# Create the music directory and give the playlist writer (nobody under root
# squashing) ownership so it can create playlist.m3u
sudo mkdir -p /export/music
sudo chown nobody:nogroup /export/music

# Add the export entry to /etc/exports (replace with your HA and Music Assistant client IPs):
# /export/music 192.168.1.10(rw,sync,no_subtree_check) 192.168.1.11(rw,sync,no_subtree_check)
# After adding the entry, reload the exports:
sudo exportfs -ra

# Start the service
sudo systemctl enable --now nfs-kernel-server
```

> [!NOTE]
> Root squashing is enabled by default on most NFS servers. Under root squashing, the Home Assistant container's root user maps to `nobody` on the server. The `chown nobody:nogroup` step ensures the playlist writer can create `playlist.m3u` inside the export. Keep root squashing enabled for security.

Place your audio files in `/export/music` (subdirectories are supported and sorted alphabetically).

## Step 2 — Mount NFS on Home Assistant Host

### HAOS (Supervised / OS)

Use the built-in network storage workflow:

1. Go to **Settings → System → Storage**.
2. Click **Add network storage**.
3. Select **NFS** as the type.
4. Enter the NFS server address (e.g., `192.168.1.X`) in the **Server** field and the share path (e.g., `/export/music`) in the **Share** field — these are separate fields in HAOS.
5. Name the storage `music` and select **Media** as the usage type, producing `/media/music`.
6. Save. Home Assistant will mount the share and make it available at `/media/music`.

### Docker / HA Core

A Docker bind mount references a path on the Docker daemon host — it does not access a remote NFS server directly. Mount the NFS share on the host first, then map it into the container:

```bash
# On the Docker host, mount the NFS share:
sudo mkdir -p /export/music
sudo mount -t nfs <nfs_server>:/export/music /export/music
```

Then add a volume mount to your `docker-compose.yml` or `docker run` command:

```yaml
volumes:
  - /export/music:/media/music:rw
```

Alternatively, use a Docker NFS volume so Docker manages the NFS mount:

```yaml
volumes:
  music_data:
    driver: local
    driver_opts:
      type: nfs
      o: "addr=<nfs_server>,rw"
      device: ":/export/music"
```

Then reference `music_data` in your service's volumes list.

## Step 2B — Music Assistant as a Standalone Docker Container (Optional)

Use this variant when Music Assistant does not run as a Home Assistant add-on — e.g., Home Assistant runs on HAOS while Music Assistant runs in Docker on a NAS or another host, or your whole stack is containerized.

The key principle: **both containers must mount the same NFS share**. `create_playlist.py` writes track paths relative to the playlist directory, so the in-container mount points may differ (e.g., `/media/music` in Home Assistant vs. `/music` in Music Assistant) as long as `playlist.m3u` lives inside the shared folder.

### 2B.1 — Mount the share into the Music Assistant container

On the Docker host that runs Music Assistant, mount the NFS share first (same as in Step 2):

```bash
# On the Music Assistant Docker host:
sudo mkdir -p /export/music
sudo mount -t nfs <nfs_server>:/export/music /export/music
```

Then add the Music Assistant service to your `docker-compose.yml`:

```yaml
services:
  music-assistant:
    image: ghcr.io/music-assistant/server:latest
    container_name: music-assistant
    restart: unless-stopped
    ports:
      - "8095:8095"
    volumes:
      - ma_data:/data
      # Same NFS share as Home Assistant, read-only is enough:
      # Music Assistant only reads audio files and the generated M3U.
      - /export/music:/music:ro
    # Alternatively, reuse the Docker-managed NFS volume from Step 2:
    # - music_data:/music:ro

volumes:
  ma_data:
```

Start it with `docker compose up -d`. The server's web interface is available at `http://<ma-host-ip>:8095`.

### 2B.2 — Add the music source in Music Assistant

1. Open the Music Assistant web interface at `http://<ma-host-ip>:8095`.
2. Go to **Settings → Providers → Add Provider** and select the **Filesystem** provider.
3. Enter the **container-internal** mount path (e.g., `/music`, not the host path) and enable **Import playlists (m3u files)** so the generated `playlist.m3u` is picked up.
4. Save. Music Assistant will scan and index the files.

### 2B.3 — Connect Home Assistant to Music Assistant

In Home Assistant, go to **Settings → Devices & Services → Add Integration → Music Assistant** and enter the server URL (`http://<ma-host-ip>:8095`). Once connected, the `music_assistant.play_media` and `music_assistant.transfer_queue` actions from Step 8 work unchanged.

> [!NOTE]
> If Home Assistant and Music Assistant run on the same Docker host in one compose stack, they can share a single Docker NFS volume (`music_data` from Step 2). If they run on different hosts, mount the NFS share on each host separately and verify `playlist.m3u` is visible at the configured path inside both containers before adding the provider.

## Step 3 — Place create_playlist.py

Copy `python_scripts/create_playlist.py` to your HA config directory:

```bash
cp python_scripts/create_playlist.py /config/
```

### Test it manually

Run the command inside the Home Assistant container (where `/config` resolves correctly), not on the host shell:

```bash
# Inside the HA container (e.g., via docker exec or the HA terminal add-on):
python3 /config/create_playlist.py /media/music /media/music/playlist.m3u
```

Or use the configured `shell_command` from Step 4 once Home Assistant has loaded it.

## Step 4 — Configure shell_command

Add to `configuration.yaml`. This command replaces the placeholder in `configuration.template.yaml`:

```yaml
shell_command:
  create_playlist: >
    python3 /config/create_playlist.py /media/music /media/music/playlist.m3u
```

Reload the `shell_command` integration via **Settings → Developer tools → YAML** (click **Reload** next to `shell_command`) or restart Home Assistant before using the command in Step 7.

## Step 5 — Set Up Music Assistant Filesystem Provider

1. Open **Music Assistant** from the HA sidebar.
2. Go to **Settings → Providers → Add Provider**.
3. Select the appropriate filesystem provider:
   - **Filesystem (local)** for a local disk — enter the mounted path (e.g., `/media/music`) in the **Path** field.
   - **Filesystem (NFS share)** for an NFS mount — enter the server IP in the **Server** field and the absolute export path (e.g., `/export/music`) in the **Path** field.
   - For a standalone Docker container (Step 2B), enter the container-internal mount path (e.g., `/music`) instead.
4. Configure:
   - **Name**: `NFS Music Library` (or any name)
   - **Import playlists (m3u files)**: Enable this setting so generated playlists are added to the library.
5. Save. Music Assistant will scan and index the files.

## Step 6 — Store Playlist Name

Add an `input_text` helper (already in `configuration.template.yaml`):

```yaml
input_text:
  media_playlist_name:
    name: "Playlist Name"
    initial: "playlist"        # ← the M3U filename without .m3u
    icon: mdi:playlist-music
```

Music Assistant matches this name against the M3U files in its configured music source.

## Step 7 — Automate Playlist Regeneration (Optional)

Create an automation to regenerate the playlist periodically (e.g., every 10 minutes) so new files are picked up automatically:

```yaml
- id: sync_media_playlist
  alias: 'Media: Sync Playlist from NFS'
  description: Regenerates the M3U playlist from the NFS audio folder.
  triggers:
    - trigger: time_pattern
      minutes: "/10"
  conditions: []
  actions:
    - action: shell_command.create_playlist
  mode: single
```

## Step 8 — Play via Automation

Use Music Assistant's `play_media` action in your automations:

```yaml
- action: music_assistant.play_media
  target:
    entity_id: media_player.<your_speaker>
  data:
    media_id: "{{ states('input_text.media_playlist_name') }}"
    media_type: playlist
    enqueue: play
```

### Multi-room Transfer

Use `music_assistant.transfer_queue` to move playback between speakers:

```yaml
- action: music_assistant.transfer_queue
  target:
    entity_id: media_player.<target_speaker>
  data:
    source_player: media_player.<source_speaker>
    auto_play: true
```

## Customization

| Setting | Where | Notes |
|---------|-------|-------|
| Audio formats | `create_playlist.py` | Add/remove extensions in `AUDIO_EXTENSIONS` tuple |
| Playlist location | `shell_command` + script args | Change `/media/music/playlist.m3u` to any path |
| Sync interval | Automation `time_pattern` | Change `"/10"` to `"/5"`, `"/30"`, etc. |
| Playlist name | `input_text.media_playlist_name` | Must match the M3U filename (without `.m3u`) |
| NFS mount path | Mount command | Change `/media/music` to any local path |

## Troubleshooting

**Playlist is empty / 0 tracks:**
- Check the NFS mount is active: `mount | grep nfs`
- Verify files exist: `ls /media/music/*.mp3`
- Run the script manually and check output

**Music Assistant doesn't see the playlist:**
- Verify the Filesystem provider path matches where the M3U is written
- Check that `input_text.media_playlist_name` matches the M3U filename
- Restart Music Assistant after adding the provider

**Standalone Docker Music Assistant sees no files:**
- Verify the share is mounted inside the container: `docker exec music-assistant ls /music`
- The provider path must be the container-internal path (e.g., `/music`), not the host path
- Check both containers see the same `playlist.m3u`: compare `ls /media/music/playlist.m3u` in Home Assistant with `ls /music/playlist.m3u` in Music Assistant

**`shell_command` fails:**
- Ensure `shell_command:` is in `configuration.yaml`
- Check HA logs for the exact error
- Verify the script has no syntax errors: `python3 -c "import py_compile; py_compile.compile('/config/create_playlist.py')"`

**NFS mount drops after reboot:**
- Add to `/etc/fstab` with `_netdev` option
- Or use HA's built-in NFS mount configuration if available
