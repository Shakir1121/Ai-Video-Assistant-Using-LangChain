import whisper
import os

# 🔥 Add ffmpeg path manually
ffmpeg_path = os.path.abspath("ffmpeg/bin")
os.environ["PATH"] += os.pathsep + ffmpeg_path

model = whisper.load_model("base")  # or "tiny" if slow

def transcribe_audio(video_path: str):
    result = model.transcribe(video_path)
    return result["text"],result["segments"]

