import subprocess
import threading
import os

YTDLP_PATH = r"C:\yt-dlp.exe"

def get_stream_url(url, callback):
    """
    Runs in a thread. Fetches the direct stream URL using yt-dlp -g.
    callback(url, error)
    """
    def run():
        try:
            cmd = [YTDLP_PATH, "-g", url]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            stream_url = result.stdout.strip()
            callback(stream_url, None)
        except Exception as e:
            callback(None, str(e))

    threading.Thread(target=run, daemon=True).start()

def download_video(url, callback):
    """
    Runs in a thread. Downloads the video to the 'downloads' folder.
    callback(file_path, error)
    """
    def run():
        try:
            if not os.path.exists("downloads"):
                os.makedirs("downloads")
            
            # Format: Best MP4 or best available
            output_template = os.path.join("downloads", "%(title)s.%(ext)s")
            cmd = [
                YTDLP_PATH, 
                "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "-o", output_template,
                "--no-playlist",
                url
            ]
            
            # We use --get-filename first to know what the file will be named
            name_cmd = [YTDLP_PATH, "--get-filename", "-o", output_template, url]
            name_result = subprocess.run(name_cmd, capture_output=True, text=True, check=True)
            expected_file = name_result.stdout.strip()

            subprocess.run(cmd, check=True)
            callback(expected_file, None)
        except Exception as e:
            callback(None, str(e))

    threading.Thread(target=run, daemon=True).start()
