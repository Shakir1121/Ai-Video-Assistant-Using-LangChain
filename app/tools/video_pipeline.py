import whisper
import ffmpeg
import tempfile
import os
import shutil
import sys


# ---------------- CROSS-PLATFORM FFMPEG RESOLUTION ----------------
# Streamlit Cloud (Linux) has system ffmpeg pre-installed.
# On Windows we use the bundled ffmpeg/bin in the repo.
def _resolve_ffmpeg():
    # 1) If "ffmpeg" is on system PATH (Linux/macOS), use it.
    which = shutil.which("ffmpeg")
    if which:
        return which

    # 2) Windows fallback: bundled binary in repo.
    if sys.platform.startswith("win"):
        win_dir = os.path.join(os.path.dirname(__file__), "..", "..", "ffmpeg", "bin")
        if os.path.exists(win_dir):
            os.environ["PATH"] += os.pathsep + win_dir
            exe = os.path.join(win_dir, "ffmpeg.exe")
            if os.path.exists(exe):
                return exe

    return "ffmpeg"


FFMPEG_CMD = _resolve_ffmpeg()


# ---------------- LAZY WHISPER MODEL LOAD ----------------
# Load Whisper model on first use (not at import time).
# This keeps the Streamlit app startup fast and avoids loading
# the ~142MB model into the 1GB memory unless the user actually analyzes.
_model = None


def _get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model


def extract_audio(video_path):
    audio_path = tempfile.mktemp(suffix=".mp3")

    try:
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, format="mp3", ac=1, ar="16000")
            .run(cmd=FFMPEG_CMD, quiet=True)
        )

        return audio_path

    except Exception as e:
        raise RuntimeError(f"FFmpeg failed: {e}")


def transcribe_video(video_path):
    audio_path = extract_audio(video_path)

    model = _get_model()
    result = model.transcribe(audio_path)

    transcript = result["text"]
    segments = result["segments"]

    clean_segments = []
    for s in segments:
        clean_segments.append({
            "start": s["start"],
            "end": s["end"],
            "text": s["text"]
        })

    return transcript, clean_segments

