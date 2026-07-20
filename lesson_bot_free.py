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
POLLINATIONS_IMAGE_BASE = "https://image.pollinations.ai/prompt/"
POLLINATIONS_TEXT_URL = "https://text.pollinations.ai/openai"


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
    url = f"{POLLINATIONS_IMAGE_BASE}{encoded_prompt}?width=1024&height=576&nologo=true"
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


def save_lessons(lessons):
    with open(LESSONS_FILE, "w") as f:
        json.dump(lessons, f, indent=2)


def generate_new_lesson(existing_topics: list) -> dict:
    """Generates one new lesson (topic, body, code, homework, image_prompt)
    using Pollinations.ai's free text API (no key needed). Returns None if
    generation or validation fails, so the caller can skip gracefully."""

    avoid_list = "; ".join(existing_topics)
    system_prompt = (
        "You are writing one lesson for a daily Solidity/smart-contract-development "
        "course delivered over Telegram. Respond with ONLY a raw JSON object, no markdown "
        "fences, no commentary, matching exactly this schema:\n"
        '{"topic": "short topic title", '
        '"body": "400-600 word explanation ending with a Further Reading section listing '
        '2-4 real URLs (official Solidity docs, Ethereum.org, OpenZeppelin docs, or a known '
        'security firm blog)", '
        '"code": "a complete, correct Solidity code example starting with '
        '// SPDX-License-Identifier: MIT and pragma solidity ^0.8.20;", '
        '"homework": "one practice task related to the topic", '
        '"image_prompt": "a short prompt for a minimalist flat-design tech illustration, '
        'blue and purple color scheme, representing the concept"}'
    )
    user_prompt = (
        "Pick ONE intermediate-to-advanced Solidity/smart-contract topic NOT already "
        f"covered in this course. Already-covered topics: {avoid_list}. "
        "Write the full lesson now as raw JSON only."
    )

    body = json.dumps({
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "model": "openai",
        "jsonMode": True,
        "private": True,
        "seed": os.urandom(4).hex(),
    }).encode("utf-8")

    req = urllib.request.Request(
        POLLINATIONS_TEXT_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8")
    except Exception as e:
        print(f"Pollinations text generation request failed: {e}")
        return None

    # The endpoint may return an OpenAI-style chat completion object,
    # or raw text depending on mode -- handle both.
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and "choices" in parsed:
            content = parsed["choices"][0]["message"]["content"]
        else:
            content = raw
    except json.JSONDecodeError:
        content = raw

    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        content = content.split("\n", 1)[-1] if "\n" in content else content

    try:
        lesson = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Could not parse generated lesson as JSON: {e}")
        return None

    required_fields = ["topic", "body", "code", "homework", "image_prompt"]
    if not all(lesson.get(f) for f in required_fields):
        print("Generated lesson missing required fields, skipping.")
        return None

    if "SPDX-License-Identifier" not in lesson["code"]:
        lesson["code"] = "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\n\n" + lesson["code"]

    if lesson["topic"].strip().lower() in [t.strip().lower() for t in existing_topics]:
        print("Generated lesson duplicates an existing topic, skipping.")
        return None

    return lesson


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

    # 5. Grow the curriculum: whenever we've just sent the LAST lesson in the
    # current rotation, generate one new lesson (free, via Pollinations.ai)
    # and append it so the list never runs out of fresh content.
    if idx == len(lessons) - 1:
        print("End of rotation reached -- generating a new lesson...")
        existing_topics = [l["topic"] for l in lessons]
        new_lesson = generate_new_lesson(existing_topics)
        if new_lesson:
            lessons.append(new_lesson)
            save_lessons(lessons)
            print(f"Added new lesson: {new_lesson['topic']} (curriculum now {len(lessons)} lessons)")
        else:
            print("Lesson generation failed or was invalid -- curriculum unchanged this run.")


if __name__ == "__main__":
    main()
