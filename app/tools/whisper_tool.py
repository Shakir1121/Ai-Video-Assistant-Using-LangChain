import whisper
import os
import shutil
import sys


# ---------------- CROSS-PLATFORM FFMPEG RESOLUTION ----------------
# Streamlit Cloud (Linux) has system ffmpeg pre-installed.
# On Windows we use the bundled ffmpeg/bin in the repo.
def _resolve_ffmpeg():
    which = shutil.which("ffmpeg")
    if which:
        return which

    if sys.platform.startswith("win"):
        win_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ffmpeg", "bin"))
        if os.path.exists(win_dir):
            os.environ["PATH"] += os.pathsep + win_dir
            exe = os.path.join(win_dir, "ffmpeg.exe")
            if os.path.exists(exe):
                return exe

    return "ffmpeg"


FFMPEG_CMD = _resolve_ffmpeg()


# ---------------- LAZY WHISPER MODEL LOAD ----------------
_model = None


def _get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model


def transcribe_audio(video_path: str):
    model = _get_model()
    result = model.transcribe(video_path)
    return result["text"], result["segments"]

