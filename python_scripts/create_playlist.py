"""
Scan a folder for audio files and generate an M3U playlist.

Called by shell_command from Home Assistant.
Usage: python3 create_playlist.py <audio_folder> <m3u_file>
"""
import os
import sys
import tempfile

AUDIO_EXTENSIONS = (".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus")

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 create_playlist.py <audio_folder> <m3u_file>")
        sys.exit(1)

    audio_folder = sys.argv[1]
    m3u_file = sys.argv[2]

    if not os.path.exists(audio_folder):
        print(f"Error: Folder '{audio_folder}' does not exist.")
        sys.exit(1)

    count = 0
    dest_dir = os.path.dirname(m3u_file) or "."
    try:
        fd, tmp_path = tempfile.mkstemp(dir=dest_dir, suffix=".m3u.tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n\n")
            for root, _dirs, files in sorted(os.walk(audio_folder)):
                for filename in sorted(files):
                    if filename.lower().endswith(AUDIO_EXTENSIONS):
                        filepath = os.path.join(root, filename)
                        relative_path = os.path.relpath(filepath, os.path.dirname(m3u_file))
                        title = os.path.splitext(filename)[0]
                        f.write(f"#EXTINF:0,{title}\n")
                        f.write(f"{relative_path}\n\n")
                        count += 1
        os.replace(tmp_path, m3u_file)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    print(f"Playlist saved to {m3u_file} ({count} tracks)")

if __name__ == "__main__":
    main()
