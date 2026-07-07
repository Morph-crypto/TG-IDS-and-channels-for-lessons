"""
Daily Solidity lesson bot - 100% free version.

No Anthropic API key needed. Lessons are pre-written and stored in
lessons.json. This script just picks the next one in rotation and
sends it to your Telegram chat.

Required environment variables (set as GitHub Actions secrets):
  TELEGRAM_BOT_TOKEN  - token from @BotFather
  TELEGRAM_CHAT_ID    - your personal chat id
"""

import os
import sys
import json
import urllib.request
import urllib.error

HERE = os.path.dirname(__file__)
LESSONS_FILE = os.path.join(HERE, "lessons.json")
STATE_FILE = os.path.join(HERE, "topic_index.json")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def load_lessons():
    with open(LESSONS_FILE) as f:
        return json.load(f)


def get_next_index(total: int) -> int:
    idx = 0
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                idx = json.load(f).get("index", 0)
        except Exception:
            idx = 0

    with open(STATE_FILE, "w") as f:
        json.dump({"index": (idx + 1) % total}, f)

    return idx % total


def send_telegram_message(text: str):
    chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)] or [text]
    for chunk in chunks:
        body = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "disable_web_page_preview": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                resp.read()
        except urllib.error.HTTPError as e:
            print("Telegram send failed:", e.read().decode("utf-8"))
            raise


def main():
    missing = [name for name, val in [
        ("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN),
        ("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID),
    ] if not val]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    lessons = load_lessons()
    idx = get_next_index(len(lessons))
    lesson = lessons[idx]

    header = f"SOLIDITY LESSON {idx + 1}/{len(lessons)}\nTopic: {lesson['topic']}\n{'-'*30}\n\n"
    send_telegram_message(header + lesson["body"])
    print(f"Sent lesson {idx + 1}: {lesson['topic']}")


if __name__ == "__main__":
    main()
