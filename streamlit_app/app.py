import streamlit as st
import sys
import os
import time

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from app.tools.video_pipeline import transcribe_video
from app.tools.notes_generator import save_notes_pdf
from app.agents.summarizer_agent import summarizer_agent_stream
from app.agents.qa_agent import qa_agent_stream
from app.memory.vector_store import store_text
from app.tools.llm_loader import create_chain

OPEN_QUESTIONS_PROMPT = """You are an expert meeting analyst. Extract ALL open questions, unresolved issues, and follow-up items from this transcript.
Format:
## Open Questions & Follow-ups
### Open Questions
- Question 1
### Follow-ups
- Follow-up 1
### Unresolved Issues
- Issue 1
Transcript:"""

open_questions_chain = create_chain(OPEN_QUESTIONS_PROMPT)

st.set_page_config(page_title="AI Video Intelligence", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")

for key in ["transcript", "video_path", "video_title", "summary", "open_questions", "processing_error"]:
    st.session_state.setdefault(key, None)
for key in ["processed", "processing"]:
    st.session_state.setdefault(key, False)

st.markdown("""
<style>
* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
html, body, [data-testid="stAppViewContainer"] { background-color: #0A0E1A; color: #E2E8F0; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1000px; }
h1 { font-size: 2.5rem !important; background: linear-gradient(135deg, #60A5FA, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.card { background: linear-gradient(135deg, #111827, #0F172A); border: 1px solid #1E293B; border-radius: 16px; padding: 24px; margin-bottom: 20px; }
.card-accent { border-left: 4px solid #3B82F6; }
.stButton > button { background: linear-gradient(135deg, #2563EB, #1D4ED8) !important; color: white !important; border: none !important; border-radius: 10px !important; padding: 10px 24px !important; font-weight: 600 !important; width: 100%; }
.stTextInput input { background-color: #1E293B !important; border: 1px solid #334155 !important; border-radius: 10px !important; color: #F1F5F9 !important; padding: 12px 16px !important; }
.stFileUploader { background: #111827 !important; border: 2px dashed #334155 !important; border-radius: 12px !important; padding: 20px !important; }
.stInfo { background-color: rgba(59,130,246,0.1) !important; color: #93C5FD !important; }
.stSuccess { background-color: rgba(34,197,94,0.1) !important; color: #86EFAC !important; }
.stError { background-color: rgba(239,68,68,0.1) !important; color: #FCA5A5 !important; }
.chat-msg { background: #1E293B; border-radius: 12px; padding: 16px; margin: 8px 0; border-left: 3px solid #3B82F6; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;}
.transcript-box { background: #1E293B; border-radius: 12px; padding: 20px; max-height: 400px; overflow-y: auto; font-size: 0.9rem; line-height: 1.6; border: 1px solid #334155; }
</style>""", unsafe_allow_html=True)

st.markdown('<div style="text-align:center;font-size:3rem;">🎬</div><h1 style="text-align:center;">AI Video Intelligence</h1><p style="color:#64748B;font-size:1.05rem;text-align:center;">Upload an audio or video file to analyze</p>', unsafe_allow_html=True)

st.markdown("""<div class="card card-accent"><div style="display:inline-block;background:rgba(59,130,246,0.15);color:#60A5FA;padding:4px 12px;border-radius:20px;font-weight:600;margin-bottom:12px;">WHAT THIS TOOL DOES</div><ul style="list-style:none;padding:0;margin:0;"><li style="padding:8px 0;color:#94A3B8;">&rarr; Takes any audio or video file as input</li><li style="padding:8px 0;color:#94A3B8;">&rarr; Transcribes audio using local Whisper AI</li><li style="padding:8px 0;color:#94A3B8;">&rarr; Generates a descriptive video title</li><li style="padding:8px 0;color:#94A3B8;">&rarr; Shows full transcript</li><li style="padding:8px 0;color:#94A3B8;">&rarr; Summarises the video content in bullet points</li><li style="padding:8px 0;color:#94A3B8;">&rarr; Extracts open questions and follow-ups</li><li style="padding:8px 0;color:#94A3B8;">&rarr; Lets you ask questions about the video with ChromaDB RAG</li><li style="padding:8px 0;color:#94A3B8;">&rarr; Export full detailed report as PDF</li></ul></div><hr>""", unsafe_allow_html=True)


def run_analysis(video_path, status, bar):
    t, _ = transcribe_video(video_path)
    st.session_state.transcript = t
    store_text(t)
    s = ""
    for c in summarizer_agent_stream(t):
        s += c
    st.session_state.summary = s
    st.session_state.open_questions = open_questions_chain.invoke({"input": t})
    st.session_state.processed = True
    st.session_state.processing = False
    status.success("Analysis complete!")
    bar.empty()
    st.rerun()


# ==================== INPUT SECTION ====================
if not st.session_state.processed:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Upload Audio / Video File")
    video_file = st.file_uploader("vid_file", type=["mp4", "mov", "avi", "mkv", "webm", "mp3", "wav", "m4a"], label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    if video_file and not st.session_state.video_path and not st.session_state.processing:
        audio_dir = os.path.join(ROOT_DIR, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        base_name, ext = os.path.splitext(video_file.name)
        safe_base = base_name.replace(" ", "_").replace("(", "").replace(")", "")
        vp = os.path.join(audio_dir, f"{int(time.time())}_{safe_base}{ext}")
        with open(vp, "wb") as f:
            f.write(video_file.read())
        st.session_state.video_path = vp
        st.session_state.video_title = base_name
        st.success(f"Saved: {base_name}{ext}")

    if st.session_state.processing_error:
        st.error(st.session_state.processing_error)

    if video_file and st.session_state.video_path and not st.session_state.processing and not st.session_state.processed:
        if st.button("Analyze Video", use_container_width=True, type="primary"):
            st.session_state.processing = True
            st.session_state.processing_error = None
            status = st.empty()
            bar = st.progress(0)
            try:
                status.info("1/2 Transcribing & analyzing...")
                bar.progress(50)
                run_analysis(st.session_state.video_path, status, bar)
            except Exception as e:
                st.session_state.processing_error = str(e)
                st.session_state.processing = False
                status.error(f"Error: {e}")
                bar.empty()

# ==================== RESULTS SECTION ====================
if st.session_state.processed and st.session_state.transcript:
    if st.button("Process Another Video", use_container_width=True):
        for k in ["transcript", "video_path", "video_title", "summary", "open_questions", "processing_error"]:
            st.session_state[k] = None
        st.session_state.processed = False
        st.session_state.processing = False
        st.rerun()

    st.markdown("<hr>")
    if st.session_state.video_title:
        st.markdown(f"## Video Details\n<div class='card'><h3>{st.session_state.video_title}</h3></div>", unsafe_allow_html=True)

    st.markdown('<div class="card"><h3>Full Transcript</h3><div class="transcript-box">' + st.session_state.transcript + '</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><h3>Video Summary</h3>' + (st.session_state.summary or '<p>No summary generated.</p>') + '</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><h3>Open Questions & Follow-ups</h3>' + (st.session_state.open_questions or '<p>No open questions identified.</p>') + '</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><h3>Ask Questions</h3><p style="color:#94A3B8;font-size:0.9rem;">Uses ChromaDB RAG to retrieve relevant context</p>', unsafe_allow_html=True)
    q = st.text_input("chat_q", placeholder="e.g., What is the main topic?", label_visibility="collapsed")
    if q:
        with st.spinner("Thinking..."):
            box = st.empty()
            r = ""
            for c in qa_agent_stream(st.session_state.transcript, q):
                r += c
                box.markdown(f'<div class="chat-msg">{r}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    report_text = f"AI VIDEO INTELLIGENCE REPORT\n\nTitle: {st.session_state.video_title or 'Untitled'}\n\nTranscript:\n{st.session_state.transcript}\n\nSummary:\n{st.session_state.summary or 'N/A'}\n\nOpen Questions:\n{st.session_state.open_questions or 'N/A'}"
    report_md = f"## Report\n\n**Title:** {st.session_state.video_title or 'Untitled'}\n\n### Transcript\n\n{st.session_state.transcript}\n\n### Summary\n\n{st.session_state.summary or 'N/A'}\n\n### Open Questions\n\n{st.session_state.open_questions or 'N/A'}"

    st.markdown('<div class="card"><h3>Export Report</h3>', unsafe_allow_html=True)
    if st.button("Generate PDF Report", use_container_width=True):
        with st.spinner("Generating PDF..."):
            pp = save_notes_pdf(report_md, "ai_video_report.pdf")
        with open(pp, "rb") as f:
            st.download_button("Download PDF", data=f, file_name="ai_video_report.pdf", mime="application/pdf", use_container_width=True)
    st.download_button("Download TXT", data=report_text, file_name="ai_video_report.txt", mime="text/plain", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state.video_path and not st.session_state.processed:
    st.markdown('<div style="text-align:center;padding:40px 20px;background:#111827;border-radius:16px;border:1px dashed #334155;"><div style="font-size:3rem;">🎯</div><h3 style="color:#94A3B8;">Ready to analyze</h3><p style="color:#64748B;">Upload an audio or video file above to get started</p></div>', unsafe_allow_html=True)

st.markdown('<hr><div style="text-align:center;color:#475569;font-size:0.85rem;">Built with Streamlit - Whisper AI - Mistral AI - ChromaDB</div>', unsafe_allow_html=True)

