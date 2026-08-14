"""
export_pdf.py
-------------
Scrapes a URL, runs it through the summarizer, and exports a clean,
professional single-page PDF report ready to send to a client.

Usage:
    python export_pdf.py <url> [mode]

    mode defaults to "competitor" if not supplied.
    Valid modes: quick | detailed | competitor

Example:
    python export_pdf.py https://www.redfin.com competitor
    python export_pdf.py https://news.ycombinator.com quick
"""

import os
import sys
import time
from datetime import date
from urllib.parse import urlparse

# Ensure stdout/stderr use UTF-8 on Windows consoles that default to legacy
# code pages (e.g. cp1256), so emoji in progress messages are rendered safely.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from scraper import scrape_url, ScrapingError
from summarizer import summarize_text, SummarizationError

# ---------------------------------------------------------------------------
# reportlab imports
# ---------------------------------------------------------------------------
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
COLOR_PRIMARY = colors.HexColor("#1C1E22")   # main body text
COLOR_MUTED   = colors.HexColor("#6B6960")   # meta / footer text
COLOR_ACCENT  = colors.HexColor("#0F6E5C")   # eyebrow label + section labels
COLOR_RULE    = colors.HexColor("#E4E1D8")   # horizontal rule


# ---------------------------------------------------------------------------
# Paragraph styles
# ---------------------------------------------------------------------------
def build_styles() -> dict:
    """Return a dict of named ParagraphStyle objects."""
    return {
        "eyebrow": ParagraphStyle(
            "eyebrow",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=COLOR_ACCENT,
            letterSpacing=1.2,
            leading=11,
            alignment=TA_LEFT,
        ),
        "date": ParagraphStyle(
            "date",
            fontName="Helvetica",
            fontSize=8,
            textColor=COLOR_MUTED,
            leading=11,
            alignment=TA_RIGHT,
        ),
        "title": ParagraphStyle(
            "title",
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=COLOR_PRIMARY,
            leading=26,
            spaceAfter=4,
        ),
        "meta": ParagraphStyle(
            "meta",
            fontName="Helvetica",
            fontSize=9,
            textColor=COLOR_MUTED,
            leading=13,
        ),
        "section_label": ParagraphStyle(
            "section_label",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=COLOR_ACCENT,
            leading=14,
            letterSpacing=0.8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=11,
            textColor=COLOR_PRIMARY,
            leading=15.4,  # ~1.4x line spacing
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Helvetica",
            fontSize=11,
            textColor=COLOR_PRIMARY,
            leading=15.4,
            leftIndent=16,
            firstLineIndent=-16,  # hanging indent aligns wrapped lines under text
            spaceAfter=3,
        ),
        "footer_left": ParagraphStyle(
            "footer_left",
            fontName="Helvetica",
            fontSize=8,
            textColor=COLOR_MUTED,
            leading=10,
            alignment=TA_LEFT,
        ),
        "footer_right": ParagraphStyle(
            "footer_right",
            fontName="Helvetica",
            fontSize=8,
            textColor=COLOR_MUTED,
            leading=10,
            alignment=TA_RIGHT,
        ),
    }


# ---------------------------------------------------------------------------
# Domain -> slug helper
# ---------------------------------------------------------------------------
def url_to_slug(url: str) -> str:
    """Convert a URL to a filename-safe slug, e.g. redfin.com -> redfin-com."""
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path  # handle URLs without scheme
    domain = domain.replace("www.", "").strip("/")
    slug = ""
    for ch in domain:
        if ch.isalnum() or ch == "-":
            slug += ch
        else:
            slug += "-"
    # Collapse consecutive hyphens
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------
def build_pdf(
    output_path: str,
    url: str,
    mode: str,
    summary: str,
    key_points: list,
    word_count: int,
    processing_time: str,
    report_date: date,
) -> None:
    """Build and save the PDF report to *output_path*."""

    styles = build_styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    story = []

    # ------------------------------------------------------------------
    # 1. Header band -- eyebrow label (left) + date (right) on same line
    # ------------------------------------------------------------------
    # Format date without zero-padding in a cross-platform way
    day = report_date.day
    date_str = report_date.strftime(f"Generated on %B {day}, %Y")

    page_width = A4[0] - 4 * cm  # usable width after left+right margins

    header_data = [
        [
            Paragraph("WEB INSIGHTS REPORT", styles["eyebrow"]),
            Paragraph(date_str, styles["date"]),
        ]
    ]
    header_table = Table(
        header_data,
        colWidths=[page_width * 0.55, page_width * 0.45],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    # ------------------------------------------------------------------
    # 2. Title -- analyzed domain
    # ------------------------------------------------------------------
    parsed = urlparse(url)
    display_title = parsed.netloc.replace("www.", "") or url
    story.append(Paragraph(display_title, styles["title"]))

    # ------------------------------------------------------------------
    # 3. Meta line -- mode * word count * processing time
    # ------------------------------------------------------------------
    meta_text = (
        f"Mode: {mode}"
        f" &nbsp;&nbsp;&middot;&nbsp;&nbsp; "
        f"Word count: {word_count:,}"
        f" &nbsp;&nbsp;&middot;&nbsp;&nbsp; "
        f"Processing time: {processing_time}"
    )
    story.append(Paragraph(meta_text, styles["meta"]))
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------------
    # 4. Horizontal rule
    # ------------------------------------------------------------------
    story.append(HRFlowable(
        width="100%",
        thickness=0.75,
        color=COLOR_RULE,
        spaceAfter=14,
    ))

    # ------------------------------------------------------------------
    # 5. Summary section
    # ------------------------------------------------------------------
    story.append(Paragraph("SUMMARY", styles["section_label"]))
    safe_summary = (
        summary
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    story.append(Paragraph(safe_summary, styles["body"]))
    story.append(Spacer(1, 18))

    # ------------------------------------------------------------------
    # 6. Key points section  (bullet "paragraph" with hanging indent)
    # ------------------------------------------------------------------
    story.append(Paragraph("KEY POINTS", styles["section_label"]))
    for point in key_points:
        safe_point = (
            point
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        bullet_para = Paragraph(
            f"\u2022 &nbsp;{safe_point}",
            styles["bullet"],
        )
        story.append(bullet_para)

    # ------------------------------------------------------------------
    # 7. Footer -- large spacer then a two-column row at the bottom
    # ------------------------------------------------------------------
    story.append(Spacer(1, 40))

    footer_data = [
        [
            Paragraph(
                "Prepared by Your Name &mdash; Web Data &amp; AI Automation",
                styles["footer_left"],
            ),
            Paragraph(
                "Powered by FastAPI + Google Gemini",
                styles["footer_right"],
            ),
        ]
    ]
    footer_table = Table(
        footer_data,
        colWidths=[page_width * 0.60, page_width * 0.40],
    )
    footer_table.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LINEABOVE",     (0, 0), (-1, 0),  0.5, COLOR_RULE),
    ]))
    story.append(footer_table)

    doc.build(story)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python export_pdf.py <url> [mode]")
        print("  mode: quick | detailed | competitor  (default: competitor)")
        sys.exit(1)

    url = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "competitor"

    print(f"Scraping and summarizing URL: {url}")
    print(f"Mode: {mode}")
    print("-" * 50)

    start_time = time.time()

    # ------------------------------------------------------------------
    # Step 1 -- Scrape
    # ------------------------------------------------------------------
    try:
        print("Scraping started...")
        scraped_text = scrape_url(url)
        word_count = len(scraped_text.split())
        print(f"Scraped {word_count} words successfully.")
    except ScrapingError as e:
        print(f"Scraping failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during scraping: {e}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 2 -- Summarize
    # ------------------------------------------------------------------
    try:
        print("Summarizing started...")
        summary_result = summarize_text(scraped_text, mode)
    except SummarizationError as e:
        print(f"Summarization failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during summarization: {e}")
        sys.exit(1)

    processing_time = f"{time.time() - start_time:.2f}s"

    summary   = summary_result["summary"]
    key_points = summary_result["key_points"]

    # ------------------------------------------------------------------
    # ALLOW_MOCK_SUMMARY warning -- identical pattern to test_competitor.py
    # ------------------------------------------------------------------
    allow_mock = os.environ.get("ALLOW_MOCK_SUMMARY", "true").lower() in ("true", "1", "yes")
    if allow_mock:
        print(
            "\n⚠️  Note: ALLOW_MOCK_SUMMARY is true — if Gemini fails, this fell back to mock data."
        )
    else:
        print(
            "\n✅  Note: ALLOW_MOCK_SUMMARY is false — this result came directly from the Gemini API."
        )

    # ------------------------------------------------------------------
    # Step 3 -- Determine output path
    # ------------------------------------------------------------------
    today = date.today()
    domain_slug = url_to_slug(url)
    date_slug   = today.strftime("%Y-%m-%d")
    filename    = f"{domain_slug}-{mode}-{date_slug}.pdf"

    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    output_path = os.path.join(reports_dir, filename)

    # ------------------------------------------------------------------
    # Step 4 -- Build PDF
    # ------------------------------------------------------------------
    print("\nGenerating PDF report...")
    build_pdf(
        output_path=output_path,
        url=url,
        mode=mode,
        summary=summary,
        key_points=key_points,
        word_count=word_count,
        processing_time=processing_time,
        report_date=today,
    )

    print(f"\n✅ Report saved to: reports/{filename}")


if __name__ == "__main__":
    main()
