import yt_dlp
import os
import re
import time
import subprocess
import sys
import shutil


AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "audio")

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
    )
    _HAS_TRANSCRIPT_API = True
except ImportError:
    _HAS_TRANSCRIPT_API = False


def _extract_video_id(url: str):
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/|embed/|shorts/|live/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def get_youtube_transcript(url: str, languages=("en", "hi", "ur", "en-US", "en-GB")):
    """
    Fetch the video's transcript/captions directly via the caption API.
    This avoids downloading video data entirely — no 403 from datacenter IPs.
    Returns a plain-text transcript string.
    Raises RuntimeError if no captions are available.
    """
    if not _HAS_TRANSCRIPT_API:
        raise RuntimeError(
            "youtube-transcript-api is not installed. Run: pip install youtube-transcript-api"
        )

    video_id = _extract_video_id(url)
    if not video_id:
        raise RuntimeError(f"Could not extract video ID from URL: {url}")

    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        try:
            transcript = transcript_list.find_transcript(languages)
        except Exception:
            # Fallback: pick the first manually created transcript
            transcript = None
            for t in transcript_list:
                if not t.is_generated:
                    transcript = t
                    break
            if transcript is None:
                for t in transcript_list:
                    transcript = t
                    break
            if transcript is None:
                raise NoTranscriptFound(video_id, languages, {})

        fetched = transcript.fetch()
        lines = [entry["text"].strip() for entry in fetched if entry.get("text")]
        return "\n".join(lines)

    except TranscriptsDisabled:
        raise RuntimeError("This video has transcripts/captions disabled by the uploader.")
    except NoTranscriptFound:
        raise RuntimeError("No captions/transcript found for this video.")
    except VideoUnavailable:
        raise RuntimeError("This video is unavailable or private.")
    except Exception as e:
        raise RuntimeError(f"Could not fetch transcript: {e}")


# ---- Robust FFmpeg path for embedded post-processing ----
def _get_ffmpeg_path():
    """Return path to ffmpeg binary (needed by yt-dlp post-processor)."""
    which = shutil.which("ffmpeg")
    if which:
        return os.path.dirname(which)
    # Windows fallback
    if sys.platform.startswith("win"):
        win_dir = os.path.join(os.path.dirname(__file__), "..", "..", "ffmpeg", "bin")
        if os.path.exists(win_dir):
            return win_dir
    return None


def ensure_audio_dir():
    os.makedirs(AUDIO_DIR, exist_ok=True)


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.strip().replace(' ', '_')
    return name[:100]


def get_youtube_title(url: str) -> str:
    """
    Extract video title using extract_flat=True to avoid triggering
    the full download extraction (which is often blocked by YouTube).
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,  # <-- key: only fetch metadata, not streams
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

    Handles 403 errors by:
      - Using extract_flat for title (avoids stream fetch on metadata)
      - Android client extraction (YouTube blocks web clients less often)
      - Multiple retries with exponential backoff
    """
    ensure_audio_dir()

    # Get the actual YouTube video title first (extract_flat = safe)
    try:
        video_title = get_youtube_title(url)
    except Exception:
        # Fallback: use URL hash as title
        video_title = "youtube_video_" + str(hash(url))[-8:]

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

    # ---- Build robust yt-dlp options ----
    ffmpeg_dir = _get_ffmpeg_path()

    ydl_opts = {
        # Format: best audio that can be extracted without re-encoding
        'format': 'bestaudio/best',
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
        'socket_timeout': 30,
        'retries': 10,
        'fragment_retries': 10,
        'extract_flat': False,
        # Use android client — YouTube is less aggressive blocking it
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'skip': ['dash', 'hls'],
            },
        },
        # Comprehensive headers
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
        },
        # Set ffmpeg location if known
        'ffmpeg_location': ffmpeg_dir,
    }

    # ---- Attempt download with retries ----
    max_attempts = 3
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Verify the mp3 file exists
            expected_path = output_path_no_ext + ".mp3"
            if os.path.exists(expected_path) and os.path.getsize(expected_path) > 5000:
                return expected_path, video_title

            # Fallback search in audio dir
            for f in os.listdir(AUDIO_DIR):
                if f.endswith(".mp3") and safe_title in f:
                    full_path = os.path.join(AUDIO_DIR, f)
                    if os.path.getsize(full_path) > 5000:
                        return full_path, video_title

            # If we got here, download happened but no file found
            raise RuntimeError("Download completed but no MP3 file found")

        except Exception as e:
            last_error = e
            error_str = str(e).lower()

            if attempt < max_attempts:
                # Wait before retry with exponential backoff
                wait = attempt * 2
                time.sleep(wait)

                # Rotate user-agent on retry
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                ]
                ydl_opts['http_headers']['User-Agent'] = user_agents[attempt % len(user_agents)]
                # Try different client on retry
                clients = [['android', 'web'], ['web'], ['android']]
                ydl_opts['extractor_args']['youtube']['player_client'] = clients[attempt % len(clients)]
            else:
                break

    # All attempts failed
    error_msg = str(last_error) if last_error else "Unknown error"
    if "403" in error_msg:
        raise RuntimeError(
            "YouTube returned a 403 Forbidden error. This is a known YouTube blocking issue. "
            "Try:\n"
            "1. Updating yt-dlp: pip install -U yt-dlp\n"
            "2. Using a different YouTube URL\n"
            "3. Or upload the video file directly instead"
        )
    raise RuntimeError(f"YouTube download failed: {error_msg}")
