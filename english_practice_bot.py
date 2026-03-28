#!/usr/bin/env python3
"""
English Speaking Practice Bot
Pulls diary entries from Notion and runs Claude-powered speaking practice sessions.

Usage:
  python english_practice_bot.py               # text mode
  python english_practice_bot.py --mode voice  # voice mode (needs SpeechRecognition)
  python english_practice_bot.py --tts         # enable text-to-speech output
  python english_practice_bot.py --days 14     # fetch last 14 days of diary

Required env vars:
  ANTHROPIC_API_KEY
  NOTION_TOKEN
  NOTION_DIARY_DATABASE_ID   (your English diary database in Notion)
"""

import os
import sys
from datetime import datetime, timezone, timedelta

import anthropic

JST = timezone(timedelta(hours=9))

# ── System prompt ──────────────────────────────────────────────────────────────
# Claude stays SHORT so the user does most of the talking (speaking practice).
SYSTEM_PROMPT = """You are a friendly English speaking practice partner for a Japanese learner.

RULES — follow strictly:
- Respond in 2-3 SHORT sentences MAXIMUM. Never write more than 3 sentences.
- Ask ONE simple follow-up question each turn to keep the conversation going.
- Correct grammar gently only when clearly wrong: say "By the way, we'd say: ..."
- Use simple, clear English (CEFR B1-B2 level). Avoid complex vocabulary.
- Be warm, encouraging, and natural — like a friend chatting.
- Never lecture. Never give lists. Just short, conversational replies.

Your goal: get the user talking as much as possible. Keep your turns brief."""


# ── Notion: fetch diary entries ─────────────────────────────────────────────
def fetch_diary_entries(days: int = 7) -> list[dict]:
    """Fetch recent diary pages from the Notion diary database."""
    try:
        from notion_client import Client
    except ImportError:
        print("Error: run  pip install notion-client", file=sys.stderr)
        sys.exit(1)

    token = os.environ.get("NOTION_TOKEN")
    db_id = os.environ.get("NOTION_DIARY_DATABASE_ID")

    if not token:
        print("Error: NOTION_TOKEN is not set.", file=sys.stderr)
        sys.exit(1)
    if not db_id:
        print("Error: NOTION_DIARY_DATABASE_ID is not set.", file=sys.stderr)
        sys.exit(1)

    notion = Client(auth=token)
    cutoff = (datetime.now(JST) - timedelta(days=days)).strftime("%Y-%m-%d")

    # Query the database — try common date property names
    results = []
    for date_prop in ("Date", "日付", "Created", "date"):
        try:
            resp = notion.databases.query(
                database_id=db_id,
                filter={"property": date_prop, "date": {"on_or_after": cutoff}},
                sorts=[{"property": date_prop, "direction": "descending"}],
                page_size=10,
            )
            results = resp.get("results", [])
            break
        except Exception:
            continue

    if not results:
        # Fallback: fetch latest 10 pages without date filter
        try:
            resp = notion.databases.query(
                database_id=db_id,
                sorts=[{"timestamp": "created_time", "direction": "descending"}],
                page_size=10,
            )
            results = resp.get("results", [])
        except Exception as e:
            print(f"Warning: could not fetch diary entries: {e}", file=sys.stderr)
            return []

    entries = []
    for page in results:
        page_id = page["id"]

        # Extract title from any title-type property
        title = ""
        for prop in page.get("properties", {}).values():
            if prop.get("type") == "title":
                title = "".join(rt.get("plain_text", "") for rt in prop.get("title", []))
                break

        # Extract date string
        date_str = page.get("created_time", "")[:10]
        for prop in page.get("properties", {}).values():
            if prop.get("type") == "date" and prop.get("date"):
                date_str = prop["date"].get("start", date_str)
                break

        # Fetch page body blocks
        try:
            blocks_resp = notion.blocks.children.list(page_id, page_size=50)
        except Exception:
            continue

        text_lines = []
        CONTENT_TYPES = {
            "paragraph", "heading_1", "heading_2", "heading_3",
            "bulleted_list_item", "numbered_list_item", "quote", "callout",
        }
        for block in blocks_resp.get("results", []):
            btype = block.get("type", "")
            if btype in CONTENT_TYPES:
                rich = block.get(btype, {}).get("rich_text", [])
                text = "".join(rt.get("plain_text", "") for rt in rich).strip()
                if text:
                    text_lines.append(text)

        if text_lines:
            entries.append(
                {
                    "title": title,
                    "date": date_str,
                    "content": "\n".join(text_lines),
                }
            )

    return entries


def build_context(entries: list[dict]) -> str:
    """Format diary entries as context for Claude."""
    if not entries:
        return (
            "No diary entries were found. "
            "Have a general English conversation with the user. "
            "Ask about their day, recent experiences, or interests."
        )

    parts = [
        "Below are the user's recent English diary entries.",
        "Use these as topics for speaking practice.",
        "Ask about specific events, feelings, and opinions they mentioned.\n",
    ]
    for entry in entries[:5]:  # cap at 5 entries
        label = f"[{entry['date']}]" if entry["date"] else ""
        title = f" — {entry['title']}" if entry["title"] else ""
        parts.append(f"--- Entry {label}{title} ---")
        parts.append(entry["content"][:600])  # truncate very long entries
        parts.append("")

    return "\n".join(parts)


# ── Claude conversation ──────────────────────────────────────────────────────
def ask_claude(messages: list[dict], context: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,  # hard cap — forces short answers
        system=f"{SYSTEM_PROMPT}\n\n{context}",
        messages=messages,
    )
    return resp.content[0].text.strip()


# ── TTS helper (optional) ────────────────────────────────────────────────────
def speak(text: str) -> None:
    """Speak text aloud. Tries pyttsx3 first, then gTTS+playsound."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 145)
        engine.say(text)
        engine.runAndWait()
        return
    except Exception:
        pass
    try:
        import tempfile, subprocess
        from gtts import gTTS
        tts = gTTS(text=text, lang="en", slow=False)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tts.save(f.name)
            subprocess.run(["mpg123", "-q", f.name], check=False)
    except Exception:
        pass  # TTS unavailable — silent fallback


# ── Input generators ─────────────────────────────────────────────────────────
def text_input():
    print("Type your answer and press Enter.  (type 'quit' to end)\n")
    while True:
        try:
            line = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        if line.lower() in ("quit", "exit", "q"):
            break
        yield line


def voice_input():
    try:
        import speech_recognition as sr
    except ImportError:
        print(
            "Error: voice mode needs SpeechRecognition.\n"
            "  pip install SpeechRecognition pyaudio",
            file=sys.stderr,
        )
        sys.exit(1)

    rec = sr.Recognizer()
    mic = sr.Microphone()

    print("Calibrating microphone... (be quiet for 1 second)")
    with mic as src:
        rec.adjust_for_ambient_noise(src, duration=1)
    print("Ready! Speak after the prompt.  (say 'quit' to end)\n")

    while True:
        print("Listening...")
        try:
            with mic as src:
                audio = rec.listen(src, timeout=8, phrase_time_limit=30)
            text = rec.recognize_google(audio, language="en-US")
            print(f"You: {text}")
            if text.lower() in ("quit", "exit"):
                break
            yield text
        except sr.WaitTimeoutError:
            print("(no speech detected — try again)")
        except sr.UnknownValueError:
            print("(could not understand — try again)")
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}", file=sys.stderr)
            break


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    import argparse

    parser = argparse.ArgumentParser(description="English Speaking Practice Bot")
    parser.add_argument(
        "--mode", choices=["text", "voice"], default="text",
        help="Input mode: text (default) or voice",
    )
    parser.add_argument(
        "--days", type=int, default=7,
        help="Days of diary history to fetch (default: 7)",
    )
    parser.add_argument(
        "--tts", action="store_true",
        help="Read Claude's responses aloud",
    )
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    # ── Fetch diary ──
    print(f"Fetching diary entries from the last {args.days} days...")
    entries = fetch_diary_entries(days=args.days)

    if entries:
        print(f"Found {len(entries)} entr{'y' if len(entries) == 1 else 'ies'}:")
        for e in entries[:5]:
            date_label = f" ({e['date']})" if e["date"] else ""
            print(f"  • {e['title'] or 'Untitled'}{date_label}")
    else:
        print("No diary entries found — starting general practice session.")

    context = build_context(entries)

    # ── Opening message ──
    print()
    print("=" * 52)
    print("  English Speaking Practice — Let's start!")
    print("=" * 52)

    history: list[dict] = []

    opening = ask_claude(
        [{"role": "user", "content": "Please start our English speaking practice. Say hi briefly and ask me about something from my diary."}],
        context,
    )
    print(f"\nClaude: {opening}\n")
    if args.tts:
        speak(opening)

    history = [
        {"role": "user", "content": "Please start our English speaking practice. Say hi briefly and ask me about something from my diary."},
        {"role": "assistant", "content": opening},
    ]

    # ── Conversation loop ──
    get_input = voice_input() if args.mode == "voice" else text_input()

    for user_text in get_input:
        history.append({"role": "user", "content": user_text})
        reply = ask_claude(history, context)
        print(f"\nClaude: {reply}\n")
        if args.tts:
            speak(reply)
        history.append({"role": "assistant", "content": reply})

    print("\nGreat practice session! See you tomorrow!")


if __name__ == "__main__":
    main()
