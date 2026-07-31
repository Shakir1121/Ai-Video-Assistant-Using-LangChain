import yt_dlp
import os
import re

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "audio")


def ensure_audio_dir():
    os.makedirs(AUDIO_DIR, exist_ok=True)


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.strip().replace(' ', '_')
    return name[:100]


def get_youtube_title(url: str) -> str:
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        },
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get('title', 'youtube_video')


def download_youtube_audio(url: str, output_path=None):
    """
    Download ONLY audio from a YouTube video and return (file_path, video_title).
    Uses the video's actual title for the filename.
    """
    ensure_audio_dir()

    # Get the actual YouTube video title first
    video_title = get_youtube_title(url)
    safe_title = sanitize_filename(video_title)

    if output_path is None:
        output_path = os.path.join(AUDIO_DIR, safe_title)

    output_path_no_ext = os.path.splitext(output_path)[0]

    # Remove any existing partial files for this video before retrying
    for f in os.listdir(AUDIO_DIR):
        if safe_title in f:
            try:
                os.remove(os.path.join(AUDIO_DIR, f))
            except OSError:
                pass

    # Add browser-like headers to avoid 403 errors
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio',
        'outtmpl': output_path_no_ext + '.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': True,
        'no_warnings': True,
        'continuedl': False,
        'buffersize': 2048,
        'socket_timeout': 60,
        'retries': 5,
        'fragment_retries': 5,
        # Add user-agent to avoid 403
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Find the mp3 file - should exist now
    expected_path = output_path_no_ext + ".mp3"
    if os.path.exists(expected_path) and os.path.getsize(expected_path) > 5000:
        return expected_path, video_title

    # Fallback search
    for f in os.listdir(AUDIO_DIR):
        if f.endswith(".mp3") and safe_title in f:
            full_path = os.path.join(AUDIO_DIR, f)
            if os.path.getsize(full_path) > 5000:
                return full_path, video_title

    # If we get here, something went wrong - raise with info
    raise RuntimeError(
        f"Download may be incomplete. Check '{AUDIO_DIR}' folder for '{safe_title}.mp3'"
    )
