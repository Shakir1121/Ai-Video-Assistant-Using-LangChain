import whisper
import ffmpeg
import tempfile
import os

# ---------------- FIX: FORCE LOCAL FFMPEG PATH ----------------
FFMPEG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "ffmpeg", "bin")
os.environ["PATH"] += os.pathsep + FFMPEG_DIR

# ---------------- WHISPER MODEL ----------------
model = whisper.load_model("base")


def extract_audio(video_path):
    audio_path = tempfile.mktemp(suffix=".mp3")

    try:
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, format="mp3", ac=1, ar="16000")
            .run(cmd=os.path.join(FFMPEG_DIR, "ffmpeg.exe"), quiet=True)
        )

        return audio_path

    except Exception as e:
        raise RuntimeError(f"FFmpeg failed: {e}")


def transcribe_video(video_path):
    audio_path = extract_audio(video_path)

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