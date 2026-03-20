#!/usr/bin/env python3
"""
Daily English Reading Report Generator
Target: ~3,600 words (30 min × 120 WPM)
"""

import anthropic
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

JST = timezone(timedelta(hours=9))

TARGET_WORDS = 3600  # 30 min × 120 WPM


def load_config(config_path: str = "config.json") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def count_words(text: str) -> int:
    # Strip markdown syntax before counting
    text = re.sub(r"[#*_`>\[\]()]", " ", text)
    words = text.split()
    return len(words)


def build_prompt(config: dict, today: str) -> str:
    interests = config.get("interests", [])
    level = config.get("level", "intermediate")
    style = config.get("style", "magazine article")
    exclude_topics = config.get("exclude_topics", [])

    interests_str = ", ".join(interests) if interests else "general knowledge, science, technology"
    exclude_str = f"\nAvoid these topics: {', '.join(exclude_topics)}." if exclude_topics else ""

    return f"""Write a daily English reading report for {today}.

REQUIREMENTS:
- Total word count: approximately {TARGET_WORDS} words (this is critical — the reader has exactly 30 minutes at 120 WPM)
- Reading level: {level} English (CEFR B2-C1 range)
- Style: {style} — engaging, not academic or dry
- Topic area: {interests_str}{exclude_str}

STRUCTURE (use these exact section headers):
1. **Today's Report** — One compelling headline and 2-3 sentence hook (around 80 words)
2. **Main Story** — Deep dive into the primary topic (around 1,800 words)
3. **Second Story** — A related or contrasting topic (around 1,200 words)
4. **Quick Takes** — 3 short items, ~100 words each (around 300 words)
5. **Word of the Day** — One advanced vocabulary word with definition, etymology, and 3 example sentences (around 120 words)

STYLE GUIDELINES:
- Use varied sentence lengths — mix short punchy sentences with longer flowing ones
- Include real-world examples, analogies, and concrete details
- Write in active voice wherever possible
- No bullet points in the main stories — use natural prose paragraphs
- Keep paragraphs to 3-5 sentences for easy reading on mobile
- Start every paragraph with a strong opening sentence

At the very end, add a line (not counted in the main text):
WORD_COUNT: [actual word count of the report body]

Make this genuinely interesting — the reader should finish their 30-minute commute wanting more."""


def generate_report(config: dict) -> tuple[str, int]:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    today = datetime.now(JST).strftime("%B %d, %Y")
    prompt = build_prompt(config, today)

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=8000,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        response = stream.get_final_message()

    content = ""
    for block in response.content:
        if block.type == "text":
            content = block.text
            break

    # Parse reported word count from the footer line
    reported_count = 0
    match = re.search(r"WORD_COUNT:\s*(\d+)", content)
    if match:
        reported_count = int(match.group(1))
        content = re.sub(r"\nWORD_COUNT:\s*\d+\s*$", "", content).rstrip()

    actual_count = count_words(content)
    word_count = reported_count if reported_count > 0 else actual_count

    return content, word_count


def save_report(content: str, word_count: int, output_dir: str = "reports") -> Path:
    now = datetime.now(JST)
    date_str = now.strftime("%Y-%m-%d")
    filename = f"{date_str}.md"
    output_path = Path(output_dir) / filename

    reading_time = round(word_count / 120)

    header = f"""---
date: {date_str}
word_count: {word_count}
reading_time: {reading_time} min
target_wpm: 120
generated_at: {now.strftime("%Y-%m-%d %H:%M JST")}
---

"""

    word_count_banner = f"""
---
**📊 Today's Stats**
- Word Count: **{word_count:,} words**
- Estimated Reading Time: **{reading_time} minutes** at 120 WPM
---

"""

    # Insert banner after the first heading
    lines = content.split("\n")
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("#"):
            insert_idx = i + 1
            break

    lines.insert(insert_idx, word_count_banner)
    full_content = header + "\n".join(lines)

    output_path.write_text(full_content, encoding="utf-8")
    return output_path


def main():
    config_path = os.environ.get("CONFIG_PATH", "config.json")

    if not Path(config_path).exists():
        print(f"Error: config file not found at {config_path}", file=sys.stderr)
        sys.exit(1)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    print(f"Generating report... target: {TARGET_WORDS} words")

    content, word_count = generate_report(config)
    output_path = save_report(content, word_count, config.get("output_dir", "reports"))

    print(f"✓ Report saved: {output_path}")
    print(f"✓ Word count: {word_count:,} words (~{round(word_count/120)} min at 120 WPM)")

    # Output path for GitHub Actions to use
    print(f"REPORT_PATH={output_path}")


if __name__ == "__main__":
    main()
