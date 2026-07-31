import os
from app.tools.llm_loader import create_chain
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# GPT NOTES GENERATOR (uses central LLM chain)
# =========================
NOTES_SYSTEM_PROMPT = """You are an expert content analyst.

Convert the transcript into PROFESSIONAL NOTES.

Instructions:
- Fix incorrect words
- Remove noise and repetition
- Structure content like real notes

Structure:

## Topic Overview
- short explanation

## Key Concepts
- bullet points

## Important Terms
- define important concepts

## Key Takeaways
- 3-5 important points

Keep it clean, accurate, and useful for revision."""

notes_chain = create_chain(NOTES_SYSTEM_PROMPT)


def generate_gpt_notes(transcript: str):
    return notes_chain.invoke({"input": transcript})


# =========================
# VIDEO TITLE GENERATOR
# =========================
TITLE_SYSTEM_PROMPT = """Based on the following transcript, generate a short, descriptive title (max 10 words) for this video."""

title_chain = create_chain(TITLE_SYSTEM_PROMPT)


def generate_video_title(transcript: str) -> str:
    title = title_chain.invoke({"input": transcript[:2000]})
    title = title.strip().replace('"', '').replace("'", "")
    return title


# =========================
# PDF EXPORT
# =========================
def save_notes_pdf(text: str, filename="ai_notes.pdf"):

    output_dir = "generated_notes"
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    story = []

    # Title
    story.append(Paragraph("<b>AI VIDEO REPORT</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    # Content
    for line in text.split("\n"):
        if line.strip():
            story.append(Paragraph(line, styles["Normal"]))
            story.append(Spacer(1, 6))

    doc.build(story)

    return file_path
