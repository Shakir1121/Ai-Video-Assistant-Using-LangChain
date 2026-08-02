import os
import re
import html
from datetime import datetime
from app.tools.llm_loader import create_chain
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4


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
# PDF EXPORT (Formatted)
# =========================

def _escape(text: str) -> str:
    """Escape HTML special chars for ReportLab Paragraph."""
    return html.escape(text, quote=False)


def _markdown_to_rich(line: str) -> str:
    """
    Convert a minimal markdown subset (**bold**, *italic*, `code`) into
    ReportLab Paragraph markup. The line is already HTML-escaped.
    """
    # Bold: **text** -> <b>text</b>
    line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
    # Italic: *text* -> <i>text</i>
    line = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", line)
    # Inline code: `text` -> <font face='Courier'>text</font>
    line = re.sub(r"`([^`]+)`", r"<font face='Courier'><b>\1</b></font>", line)
    return line


def save_notes_pdf(text: str, filename="ai_notes.pdf"):

    output_dir = "generated_notes"
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=24,
        leading=28,
        spaceAfter=6,
        textColor=colors.HexColor("#1E3A8A"),
        alignment=1,  # center
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748B"),
        alignment=1,
        spaceAfter=18,
    )
    h1_style = ParagraphStyle(
        "ReportH1",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        spaceBefore=16,
        spaceAfter=8,
        textColor=colors.HexColor("#1E3A8A"),
    )
    h2_style = ParagraphStyle(
        "ReportH2",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.HexColor("#334155"),
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontSize=10.5,
        leading=15,
        spaceAfter=6,
        textColor=colors.HexColor("#1F2937"),
    )
    bullet_style = ParagraphStyle(
        "ReportBullet",
        parent=body_style,
        leftIndent=18,
        bulletIndent=6,
        spaceAfter=4,
    )

    story = []

    # ---- Cover Header ----
    story.append(Paragraph("AI VIDEO INTELLIGENCE REPORT", title_style))
    story.append(
        Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#3B82F6")))

    # ---- Parse markdown-ish content ----
    for raw_line in text.split("\n"):
        line = raw_line.strip()

        if not line:
            story.append(Spacer(1, 6))
            continue

        # ---- Horizontal rules ----
        if line in ("---", "***", "___"):
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1")))
            story.append(Spacer(1, 6))
            continue

        escaped = _escape(line)
        rich = _markdown_to_rich(escaped)

        # ---- H1 (## ) ----
        if line.startswith("## "):
            story.append(Paragraph(rich[3:], h1_style))
            story.append(HRFlowable(width="30%", thickness=2, color=colors.HexColor("#3B82F6")))
            story.append(Spacer(1, 4))
            continue

        # ---- H2 (### ) ----
        if line.startswith("### "):
            story.append(Paragraph(rich[4:], h2_style))
            continue

        # ---- Bullet / numbered lists ----
        bullet_match = re.match(r"^[-*•]\s+(.*)$", line)
        if bullet_match:
            story.append(Paragraph(rich, bullet_style, bulletText="•"))
            continue

        num_match = re.match(r"^(\d+)[.)]\s+(.*)$", line)
        if num_match:
            story.append(
                Paragraph(
                    f"<b>{num_match.group(1)}.</b> {_markdown_to_rich(_escape(num_match.group(2)))}",
                    bullet_style,
                    bulletText="•",
                )
            )
            continue

        # ---- Checkbox-style task (e.g. "[ ]" or "[x]") ----
        check_match = re.match(r"^[-*]?\s*\[([ xX])\]\s+(.*)$", line)
        if check_match:
            mark = "☑" if check_match.group(1).lower() == "x" else "☐"
            story.append(
                Paragraph(
                    f"{mark} {_markdown_to_rich(_escape(check_match.group(2)))}",
                    bullet_style,
                )
            )
            continue

        # ---- Default paragraph ----
        story.append(Paragraph(rich, body_style))

    # ---- Footer ----
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1")))
    story.append(
        Paragraph(
            "Generated by <b>AI Video Intelligence</b> — powered by Whisper AI, Mistral AI &amp; ChromaDB",
            subtitle_style,
        )
    )

    doc.build(story)

    return file_path

