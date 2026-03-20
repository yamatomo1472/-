#!/usr/bin/env python3
"""
Daily English Reading Report Generator
Target: ~3,600 words (30 min × 120 WPM)
Output: Markdown + PDF + Email + Notion
"""

import anthropic
import json
import os
import re
import smtplib
import sys
from datetime import datetime, timezone, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

JST = timezone(timedelta(hours=9))
TARGET_WORDS = 3600  # 30 min × 120 WPM

# Topics to rotate through (indices into config["interests"])
# Each day a subset is featured based on day-of-week
DAILY_TOPIC_ROTATION = {
    0: [0, 1, 5],   # Monday:    World news + Business + AI
    1: [0, 3, 6],   # Tuesday:   World news + Startups + Finance trends
    2: [0, 4, 10],  # Wednesday: World news + Commodities + Geopolitics
    3: [0, 7, 8],   # Thursday:  World news + Finance + Finance basics
    4: [0, 2, 9],   # Friday:    World news + Side biz + Risk mgmt
    5: [0, 11, 6],  # Saturday:  World news + Japan real estate + Finance
    6: [0, 5, 6],   # Sunday:    World news + AI + Finance (weekly review)
}


def load_config(config_path: str = "config.json") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def count_words(text: str) -> int:
    text = re.sub(r"[#*_`>\[\]()\-]", " ", text)
    return len(text.split())


def build_prompt(config: dict, today: str, weekday: int) -> str:
    all_interests = config.get("interests", [])
    level = config.get("level", "intermediate")
    featured_indices = DAILY_TOPIC_ROTATION.get(weekday, [0, 1, 4])
    featured = [all_interests[i] for i in featured_indices if i < len(all_interests)]

    # World news is always the anchor
    anchor = featured[0] if featured else "World and Japan news"
    secondary = featured[1] if len(featured) > 1 else "business"
    quick_topics = featured[2:] + [t for i, t in enumerate(all_interests) if i not in featured_indices]

    quick_take_topics = ", ".join(quick_topics[:3]) if quick_topics else "technology, finance, Japan economy"

    return f"""You are writing a daily English reading report for a Japanese professional learning English.
Today's date: {today}

MISSION: Create a single, cohesive report of approximately {TARGET_WORDS} words.
The reader has exactly 30 minutes on the train and reads at 120 WPM.
Word count accuracy is critical — being too short (under 3,400) or too long (over 3,800) wastes their study time.

READER PROFILE:
- Japanese business professional, early-to-mid career
- English level: {level} (CEFR B2) — can handle real business English, not ESL-simplified
- Reads every morning commute to improve reading speed AND stay informed
- Motivated by practical knowledge they can use at work

TODAY'S FEATURED TOPICS:
- Main Story (anchor): {anchor}
- Second Story: {secondary}
- Quick Takes: {quick_take_topics}

---

STRUCTURE — follow exactly:

## 📰 [Engaging headline that captures today's biggest story]

*{today} — Daily Briefing*

**[One-paragraph hook, 60-80 words, creates urgency or curiosity]**

---

## Main Story: [Specific headline]

[Deep, well-researched article on the anchor topic. Include:
- Current real-world developments as of early 2026
- Concrete numbers, company names, and data points where relevant
- Analysis, not just facts — what does this mean?
- Implications for Japanese professionals
- 1,750-1,850 words]

---

## Second Story: [Specific headline]

[Engaging article on the secondary topic. Include:
- Specific, actionable insights
- Real examples and case studies
- Clear takeaways for someone who wants to act on this information
- 1,150-1,250 words]

---

## ⚡ Quick Takes

**[Short item 1 title]**
[90-110 words on topic from: {quick_take_topics}. One sharp insight.]

**[Short item 2 title]**
[90-110 words on a different aspect of the same area or adjacent topic.]

**[Short item 3 title]**
[90-110 words. Can be a Japan-specific angle on a global story.]

---

## 📖 Word of the Day

**[Advanced business/finance/tech vocabulary word]**

*[Part of speech] | [Pronunciation guide] | Origin: [etymology in one sentence]*

**Definition:** [Clear, precise definition in 1-2 sentences]

**In context:**
1. "[Example sentence from a news/business context]"
2. "[Example sentence showing a different usage]"
3. "[Example sentence the reader could use themselves at work]"

**Why it matters:** [1-2 sentences on why this word appears frequently in business/financial English]

---

STYLE RULES:
- Write like The Economist meets Bloomberg Businessweek — authoritative but readable
- No bullet points in Main Story or Second Story — use flowing prose paragraphs
- Paragraphs: 3-5 sentences, strong opening sentence each time
- Vary sentence rhythm: mix punchy short sentences with complex longer ones
- Active voice by default; passive only when the subject is unknown
- No hedging language like "it could be argued" or "some might say"
- Reference real organizations, people, and events from 2025-early 2026

FINAL LINE (do not include in the report body, just add at the very end):
WORD_COUNT: [integer count of words in the entire report body above]"""


def generate_report(config: dict) -> tuple[str, int]:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    now = datetime.now(JST)
    today = now.strftime("%B %d, %Y")
    weekday = now.weekday()  # 0=Monday

    prompt = build_prompt(config, today, weekday)
    print(f"  Requesting report for {today} (weekday={weekday})...")

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        response = stream.get_final_message()

    content = ""
    for block in response.content:
        if block.type == "text":
            content = block.text
            break

    # Parse and strip the footer word count
    reported_count = 0
    match = re.search(r"WORD_COUNT:\s*(\d+)", content)
    if match:
        reported_count = int(match.group(1))
        content = re.sub(r"\nWORD_COUNT:\s*\d+\s*$", "", content).rstrip()

    actual_count = count_words(content)
    word_count = reported_count if reported_count > 0 else actual_count
    return content, word_count


def save_markdown(content: str, word_count: int, output_dir: str) -> Path:
    now = datetime.now(JST)
    date_str = now.strftime("%Y-%m-%d")
    output_path = Path(output_dir) / f"{date_str}.md"

    reading_time = round(word_count / 120)

    frontmatter = f"""---
date: {date_str}
word_count: {word_count}
reading_time: {reading_time} min
target_wpm: 120
generated_at: {now.strftime("%Y-%m-%d %H:%M JST")}
---

"""
    stats_banner = f"""
---
**📊 Today's Stats:** {word_count:,} words &nbsp;|&nbsp; {reading_time} min at 120 WPM
---

"""
    # Insert stats after first heading
    lines = content.split("\n")
    insert_idx = next((i + 1 for i, l in enumerate(lines) if l.startswith("#")), 0)
    lines.insert(insert_idx, stats_banner)

    output_path.write_text(frontmatter + "\n".join(lines), encoding="utf-8")
    return output_path


def save_pdf(md_path: Path, word_count: int) -> Path:
    """Convert markdown to a styled PDF using WeasyPrint."""
    try:
        import markdown as md_lib
        from weasyprint import HTML, CSS
    except ImportError:
        print("  Skipping PDF: install 'markdown' and 'weasyprint'", file=sys.stderr)
        return None

    now = datetime.now(JST)
    reading_time = round(word_count / 120)
    date_str = now.strftime("%Y-%m-%d")
    pdf_path = md_path.with_suffix(".pdf")

    raw_md = md_path.read_text(encoding="utf-8")
    # Strip YAML frontmatter for PDF rendering
    raw_md = re.sub(r"^---\n.*?\n---\n", "", raw_md, flags=re.DOTALL)

    html_body = md_lib.markdown(
        raw_md,
        extensions=["extra", "tables", "toc", "nl2br"],
    )

    css = CSS(string="""
        @page {
            size: A4;
            margin: 22mm 20mm 22mm 20mm;
            @bottom-center {
                content: counter(page) " / " counter(pages);
                font-size: 9pt;
                color: #888;
                font-family: 'Georgia', serif;
            }
        }
        body {
            font-family: 'Georgia', 'Times New Roman', serif;
            font-size: 11pt;
            line-height: 1.75;
            color: #1a1a1a;
            max-width: 100%;
        }
        h1 {
            font-size: 20pt;
            font-weight: bold;
            color: #111;
            margin-top: 0;
            margin-bottom: 4pt;
            line-height: 1.3;
            border-bottom: 2.5pt solid #1a1a1a;
            padding-bottom: 6pt;
        }
        h2 {
            font-size: 14pt;
            font-weight: bold;
            color: #1a1a1a;
            margin-top: 20pt;
            margin-bottom: 6pt;
            border-left: 4pt solid #2563eb;
            padding-left: 8pt;
        }
        h3 {
            font-size: 11.5pt;
            font-weight: bold;
            color: #333;
            margin-top: 12pt;
            margin-bottom: 4pt;
        }
        p {
            margin: 0 0 9pt 0;
            text-align: justify;
            hyphens: auto;
        }
        em {
            font-style: italic;
            color: #444;
        }
        strong {
            font-weight: bold;
        }
        hr {
            border: none;
            border-top: 1pt solid #ddd;
            margin: 14pt 0;
        }
        blockquote {
            border-left: 3pt solid #2563eb;
            margin: 10pt 0;
            padding: 4pt 12pt;
            background: #f0f4ff;
            color: #333;
        }
        code {
            font-family: 'Courier New', monospace;
            font-size: 9.5pt;
            background: #f5f5f5;
            padding: 1pt 3pt;
            border-radius: 2pt;
        }
        .stats-banner {
            background: #f0f4ff;
            border: 1pt solid #2563eb;
            border-radius: 4pt;
            padding: 6pt 10pt;
            margin: 8pt 0 16pt 0;
            font-size: 10pt;
            color: #1e3a8a;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 10pt 0;
            font-size: 10pt;
        }
        th {
            background: #1a1a1a;
            color: white;
            padding: 5pt 8pt;
            text-align: left;
        }
        td {
            border-bottom: 0.5pt solid #ddd;
            padding: 4pt 8pt;
        }
    """)

    # Wrap in full HTML document
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Daily English Report — {date_str}</title>
</head>
<body>
<div style="background:#f0f4ff;border:1pt solid #2563eb;border-radius:4pt;
     padding:6pt 10pt;margin:0 0 16pt 0;font-size:10pt;color:#1e3a8a;
     font-family:Georgia,serif;">
📊 <strong>Today's Stats:</strong> {word_count:,} words
&nbsp;|&nbsp; {reading_time} min at 120 WPM
&nbsp;|&nbsp; {date_str}
</div>
{html_body}
</body>
</html>"""

    HTML(string=html_doc).write_pdf(str(pdf_path), stylesheets=[css])
    return pdf_path


def send_email(pdf_path: Path, word_count: int) -> bool:
    """Send the PDF report via Gmail SMTP."""
    gmail_address = os.environ.get("GMAIL_ADDRESS")
    gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("RECIPIENT_EMAIL", gmail_address)

    if not gmail_address or not gmail_app_password:
        print("  Skipping email: GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set")
        return False

    now = datetime.now(JST)
    date_str = now.strftime("%Y-%m-%d")
    weekday_name = now.strftime("%A")
    reading_time = round(word_count / 120)

    msg = MIMEMultipart()
    msg["From"] = gmail_address
    msg["To"] = recipient
    msg["Subject"] = f"📖 Daily English Report — {date_str} ({weekday_name})"

    body = f"""\
Good morning!

Today's English reading report is attached.

📊 Stats
  Date       : {date_str} ({weekday_name})
  Word count : {word_count:,} words
  Reading time: {reading_time} minutes at 120 WPM

Open the PDF and enjoy your commute reading!

---
Daily English Report • Generated by Claude claude-opus-4-6
"""
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with open(pdf_path, "rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="pdf")
        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=f"english-report-{date_str}.pdf",
        )
        msg.attach(attachment)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_address, gmail_app_password)
        smtp.sendmail(gmail_address, recipient, msg.as_string())

    return True


def _rich_text(text: str, bold: bool = False, italic: bool = False) -> dict:
    """Build a single Notion rich text segment."""
    obj: dict = {"type": "text", "text": {"content": text[:2000]}}
    if bold or italic:
        obj["annotations"] = {"bold": bold, "italic": italic}
    return obj


def _parse_inline(text: str) -> list[dict]:
    """Convert inline **bold** / *italic* markdown to Notion rich text array."""
    parts = []
    # Match **bold**, *italic*, or plain spans
    for m in re.finditer(r"(\*\*(.+?)\*\*|\*(.+?)\*|([^*]+))", text):
        if m.group(2):
            parts.append(_rich_text(m.group(2), bold=True))
        elif m.group(3):
            parts.append(_rich_text(m.group(3), italic=True))
        elif m.group(4):
            parts.append(_rich_text(m.group(4)))
    return parts or [_rich_text(text)]


def _para(rich: list[dict]) -> dict:
    return {"object": "block", "type": "paragraph",
            "paragraph": {"rich_text": rich}}


def _heading(text: str, level: int) -> dict:
    kind = f"heading_{level}"
    return {"object": "block", "type": kind,
            kind: {"rich_text": _parse_inline(text)}}


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def _callout(text: str, emoji: str = "📊") -> dict:
    return {"object": "block", "type": "callout",
            "callout": {"icon": {"type": "emoji", "emoji": emoji},
                        "rich_text": _parse_inline(text)}}


def markdown_to_notion_blocks(md_text: str, word_count: int, date_str: str) -> list[dict]:
    """Convert the report markdown to a flat list of Notion blocks."""
    now = datetime.now(JST)
    reading_time = round(word_count / 120)

    blocks: list[dict] = [
        _callout(
            f"📊 {word_count:,} words  |  {reading_time} min at 120 WPM  |  {date_str}",
            "📖",
        ),
    ]

    # Strip YAML frontmatter
    clean = re.sub(r"^---\n.*?\n---\n", "", md_text, flags=re.DOTALL)

    # Group lines into logical elements (blank-line delimited)
    elements: list[str] = []
    buf: list[str] = []
    for line in clean.splitlines():
        stripped = line.rstrip()
        if stripped == "":
            if buf:
                elements.append("\n".join(buf))
                buf = []
        else:
            buf.append(stripped)
    if buf:
        elements.append("\n".join(buf))

    for elem in elements:
        # Already-inlined stats banner — skip (we added the callout above)
        if "Today's Stats" in elem and "WPM" in elem:
            continue
        # Divider
        if re.fullmatch(r"-{3,}", elem.strip()):
            blocks.append(_divider())
            continue
        # Headings
        if elem.startswith("### "):
            blocks.append(_heading(elem[4:].strip(), 3))
        elif elem.startswith("## "):
            blocks.append(_heading(elem[3:].strip(), 2))
        elif elem.startswith("# "):
            blocks.append(_heading(elem[2:].strip(), 1))
        else:
            # Multi-line element → each line as a paragraph (Notion has no
            # multi-line paragraph concept; blank lines already split elements)
            for line in elem.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Pure italic line (e.g. *March 20, 2026 — Daily Briefing*)
                m_italic = re.fullmatch(r"\*(.+)\*", line)
                if m_italic:
                    blocks.append(_para([_rich_text(m_italic.group(1), italic=True)]))
                else:
                    blocks.append(_para(_parse_inline(line)))

    return blocks


def send_to_notion(md_path: Path, word_count: int) -> bool:
    """Create a new Notion page with the report content."""
    try:
        from notion_client import Client
    except ImportError:
        print("  Skipping Notion: install 'notion-client'", file=sys.stderr)
        return False

    token = os.environ.get("NOTION_TOKEN")
    parent_id = os.environ.get("NOTION_PAGE_ID")
    if not token or not parent_id:
        print("  Skipping Notion: NOTION_TOKEN or NOTION_PAGE_ID not set")
        return False

    notion = Client(auth=token)
    now = datetime.now(JST)
    date_str = now.strftime("%Y-%m-%d")
    weekday = now.strftime("%A")

    raw_md = md_path.read_text(encoding="utf-8")
    blocks = markdown_to_notion_blocks(raw_md, word_count, date_str)

    # Create the page (Notion allows max 100 children per create call)
    response = notion.pages.create(
        parent={"page_id": parent_id.replace("-", "")},
        icon={"type": "emoji", "emoji": "📖"},
        properties={
            "title": {
                "title": [
                    {"text": {"content": f"Daily English Report — {date_str} ({weekday})"}}
                ]
            }
        },
        children=blocks[:100],
    )

    # Append remaining blocks in batches of 100
    page_id = response["id"]
    for i in range(100, len(blocks), 100):
        notion.blocks.children.append(page_id, children=blocks[i : i + 100])

    page_url = response.get("url", "")
    print(f"  Notion page URL: {page_url}")
    return True


def main():
    config_path = os.environ.get("CONFIG_PATH", "config.json")

    if not Path(config_path).exists():
        print(f"Error: config file not found at {config_path}", file=sys.stderr)
        sys.exit(1)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    output_dir = config.get("output_dir", "reports")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"Generating report... target: {TARGET_WORDS} words")
    content, word_count = generate_report(config)

    md_path = save_markdown(content, word_count, output_dir)
    print(f"✓ Markdown: {md_path}")
    print(f"✓ Word count: {word_count:,} (~{round(word_count/120)} min at 120 WPM)")

    pdf_path = None
    if config.get("pdf", True):
        pdf_path = save_pdf(md_path, word_count)
        if pdf_path:
            print(f"✓ PDF: {pdf_path}")

    if pdf_path and config.get("email", False):
        ok = send_email(pdf_path, word_count)
        if ok:
            print(f"✓ Email sent to {os.environ.get('RECIPIENT_EMAIL', os.environ.get('GMAIL_ADDRESS', '?'))}")

    if config.get("notion", True):
        ok = send_to_notion(md_path, word_count)
        if ok:
            print("✓ Notion page created")

    # For GitHub Actions step output
    print(f"REPORT_PATH={md_path}")


if __name__ == "__main__":
    main()
