# Solidity Daily Lesson Bot (100% Free Version)

Sends a Solidity/smart-contract lesson via Telegram, 3x a day, at
10:00 / 14:00 / 17:00 GMT+3. Fully free forever — no API key, no paid
services. 25 lessons are pre-written in `lessons.json` and the bot just
rotates through them, sending to either your personal chat or a Telegram
channel.

## Setup (about 5-10 minutes, one time)

### 1. Create your Telegram bot
1. Open Telegram, search for **@BotFather**, start a chat.
2. Send `/newbot`, follow the prompts (choose a name and a username ending in `bot`).
3. BotFather gives you a token like `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxx`.
   Save this — it's your `TELEGRAM_BOT_TOKEN`.

### 2. Get your `TELEGRAM_CHAT_ID`

Pick ONE of these, depending on where you want lessons sent:

#### Option A: Send to yourself (personal chat)
1. Find your bot on Telegram (by the username you gave it) and send it any
   message, e.g. "hi". This step is required — a bot can't message you until
   you've messaged it first.
2. In your browser, visit (swap in your real token):
   `https://api.telegram.org/botTOKEN/getUpdates`
3. Look for `"chat":{"id":123456789,...}` in the response. That number is
   your `TELEGRAM_CHAT_ID`.
4. Quicker alternative: message **@userinfobot** on Telegram — it instantly
   replies with your numeric user ID, which works the same way as a chat ID.

#### Option B: Send to a Telegram channel
1. Create a Telegram channel (public or private).
2. Add your bot as an **admin** of the channel: Channel settings →
   Administrators → Add Admin → search your bot's username → give it
   permission to post messages.
3. Get the channel's ID:
   - **Public channel**: just use its handle directly, e.g.
     `TELEGRAM_CHAT_ID = @mysolidity_lessons` — no lookup needed.
   - **Private channel**: post any message in the channel, then forward that
     message to **@userinfobot** (or **@RawDataBot**). It will show the
     channel's numeric ID, which looks like `-1001234567890` (note the
     minus sign — keep it).

### 3. Push this project to a GitHub repo
1. Create a new **private** GitHub repo (private so your chat ID isn't
   visible to strangers in Actions logs).
2. Upload/push all files in this folder to that repo.

### 4. Add your secrets
In your repo: **Settings → Secrets and variables → Actions → New repository secret**.
Add both:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 5. Test it
Go to the **Actions** tab → **Daily Solidity Lessons** → **Run workflow**
(this is the `workflow_dispatch` trigger). It should run in under a minute
and you should see a message land in your chat or channel.

### 6. Done
The schedule in `.github/workflows/daily_lessons.yml` runs automatically
every day at 07:00, 11:00, and 14:00 UTC (= 10:00, 14:00, 17:00 GMT+3),
sending the next lesson in rotation from `lessons.json` each time.

## Customizing
- **Edit or add lessons**: open `lessons.json` — each entry has a `topic`
  and a `body` with a code example and further-reading links.
- **Change times**: edit the `cron` lines in
  `.github/workflows/daily_lessons.yml`. Cron format is
  `minute hour day month weekday`, always in UTC.
- **Switch destination later**: just update the `TELEGRAM_CHAT_ID` secret —
  no code changes needed to move between personal chat and channel.

## Notes
- There are 25 lessons; at 3/day the rotation loops back to lesson 1 after
  about 8 days. `topic_index.json` tracks where you are and is committed
  back to the repo automatically after each run.
- GitHub Actions free tier includes 2,000 minutes/month for private repos —
  this workflow uses well under a minute per run.
- GitHub's scheduled triggers can occasionally fire a few minutes late during
  high load; this is a GitHub platform limitation, not something in this code.
