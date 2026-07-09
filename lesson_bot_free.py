"""
Daily Solidity lesson bot - 100% free version, with code file attachments
and homework tasks.

No API key needed. Lessons, code examples, and homework are all
pre-written in lessons.json. This script:
  1. Picks the next lesson in rotation
  2. Sends the explanation as a Telegram text message
  3. Sends the code example as an actual .sol file attachment
  4. Sends the homework task as a follow-up message

Required environment variables (set as GitHub Actions secrets):
  TELEGRAM_BOT_TOKEN  - token from @BotFather
  TELEGRAM_CHAT_ID    - your personal chat id or channel id/@handle
"""

import os
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
import mimetypes
import uuid

HERE = os.path.dirname(__file__)
LESSONS_FILE = os.path.join(HERE, "lessons.json")
STATE_FILE = os.path.join(HERE, "topic_index.json")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Pollinations.ai — free, open-source, no API key or signup required.
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"


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
            print("Telegram sendMessage failed:", e.read().decode("utf-8"))
            raise


def fetch_pollinations_image(prompt: str) -> bytes:
    """Fetches a free AI-generated image from Pollinations.ai (no key needed)."""
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"{POLLINATIONS_BASE}{encoded_prompt}?width=1024&height=576&nologo=true"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def send_telegram_photo(image_bytes: bytes, caption: str = ""):
    boundary = uuid.uuid4().hex

    parts = []
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{TELEGRAM_CHAT_ID}\r\n')
    if caption:
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n')
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="photo"; filename="lesson.jpg"\r\n'
        f'Content-Type: image/jpeg\r\n\r\n'
    )

    body = "".join(parts).encode("utf-8") + image_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        print("Telegram sendPhoto failed:", e.read().decode("utf-8"))
        raise


def send_telegram_document(filename: str, content: str, caption: str = ""):
    """Sends a text file as a document attachment using multipart/form-data,
    built manually so no extra pip dependencies (like 'requests') are needed."""
    boundary = uuid.uuid4().hex
    file_bytes = content.encode("utf-8")

    parts = []
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{TELEGRAM_CHAT_ID}\r\n')
    if caption:
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n')
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="{filename}"\r\n'
        f'Content-Type: {mimetypes.guess_type(filename)[0] or "text/plain"}\r\n\r\n'
    )

    body = "".join(parts).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        print("Telegram sendDocument failed:", e.read().decode("utf-8"))
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

    # 1. Illustrative image (free, via Pollinations.ai)
    image_prompt = lesson.get(
        "image_prompt",
        f"minimalist flat-design tech illustration representing the concept of {lesson['topic']}, blue and purple color scheme, clean vector style"
    )
    try:
        image_bytes = fetch_pollinations_image(image_prompt)
        send_telegram_photo(image_bytes, caption=f"Lesson {idx + 1}: {lesson['topic']}")
    except Exception as e:
        print(f"Image generation/send failed, continuing without image: {e}")

    # 2. Lesson explanation
    header = f"SOLIDITY LESSON {idx + 1}/{len(lessons)}\nTopic: {lesson['topic']}\n{'-'*30}\n\n"
    send_telegram_message(header + lesson["body"])

    # 3. Code example as a real .sol file
    if lesson.get("code"):
        filename = f"lesson_{idx + 1}_example.sol"
        send_telegram_document(filename, lesson["code"], caption=f"Code example for: {lesson['topic']}")

    # 4. Homework
    if lesson.get("homework"):
        send_telegram_message(f"HOMEWORK\n{'-'*30}\n\n{lesson['homework']}")

    print(f"Sent lesson {idx + 1}: {lesson['topic']}")


if __name__ == "__main__":
    main()
