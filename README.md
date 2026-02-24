# ✈️ Aviation Job Bot

A Telegram bot that fetches daily job listings relevant to Air Transport Management graduates — covering aviation operations, project management, and data analysis roles.

## Features

- 📬 Daily job digest at **9:00 AM SGT** automatically
- 🔍 `/latest` command to fetch jobs on demand
- 🎓 Shows relevant **ATM degree skills** per job listing
- 🌐 Sources: **MyCareersFuture**, **LinkedIn**, **Indeed**, and major aviation company career portals (SIA, Changi Airport, SATS, ST Engineering, CAAS)
- 🏆 Jobs ranked by relevance to your background

---

## Setup Guide

### Step 1 — Create your Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **Bot Token** (looks like `123456789:ABCdef...`)

### Step 2 — Deploy to Railway

1. Push this project to a **GitHub repository**
2. Go to [railway.app](https://railway.app) and sign up/log in
3. Click **New Project → Deploy from GitHub repo** and select your repo
4. Railway will detect `railway.toml` automatically
5. Go to your service → **Variables** tab and add:
   - `TELEGRAM_BOT_TOKEN` → your bot token from Step 1
6. Railway will build and deploy automatically — your bot will be live in ~1 minute!

### Step 3 — Subscribe

Once the bot is live, anyone can start receiving daily updates by messaging it:
1. Open the bot on Telegram
2. Send `/start`
3. Send `/subscribe`

That's it — no chat IDs needed. Anyone who subscribes will get updates at 9AM, 12PM, and 3PM SGT.

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"

# Run
python bot.py
```

---

## Project Structure

```
aviation-job-bot/
├── bot.py          # Telegram bot logic + scheduler
├── scraper.py      # Job fetching from all sources
├── formatter.py    # Message formatting + ATM skill matching
├── requirements.txt
├── railway.toml    # Railway deployment config
└── README.md
```

---

## Job Sources

| Source | Notes |
|--------|-------|
| MyCareersFuture | Singapore government jobs portal (API-based) |
| Indeed | Web scraping (sg.indeed.com) |
| LinkedIn | Web scraping (public listings) |
| Singapore Airlines | Direct career portal |
| Changi Airport Group | Direct career portal |
| SATS Ltd | Ground handling & aviation services |
| ST Engineering | Aerospace & engineering |
| CAAS | Civil Aviation Authority of Singapore |

---

## ATM Degree Skills Matched

The bot automatically identifies skills from your Air Transport Management degree that are relevant to each job, including:

- Aviation Safety & Security
- Airline Strategy & Economics
- Airport Planning & Management
- Revenue & Network Management
- Data Analysis & Forecasting
- Project & Operations Management
- ICAO/IATA Regulations
- Cargo & Logistics Management

---

## Notes

- LinkedIn and Indeed may occasionally block scrapers; the bot handles errors gracefully and continues with other sources.
- For best results on Render, use the **Worker** service type (not Web Service) since the bot doesn't need to listen on a port.
- The scheduler uses `APScheduler` with SGT timezone to ensure the 9 AM trigger is always accurate.
