import os
import json
import logging
import asyncio
from telegram import Update, Bot, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from scraper import fetch_all_jobs
from formatter import format_jobs_message

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
# TELEGRAM_CHAT_ID kept for backwards compatibility — owner is always pre-seeded as a subscriber.
OWNER_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
SGT = pytz.timezone("Asia/Singapore")

# ─── Bot Command Menu ─────────────────────────────────────────────────────────
# These show up when users type "/" in the Telegram keyboard.
BOT_COMMANDS = [
    BotCommand("start",       "Show welcome message and bot info"),
    BotCommand("subscribe",   "Start receiving daily job updates (9AM, 12PM, 3PM SGT)"),
    BotCommand("unsubscribe", "Stop receiving daily job updates"),
    BotCommand("status",      "Check if you are subscribed"),
    BotCommand("latest",      "Fetch the latest job listings right now"),
]

# ─── Subscriber Store ────────────────────────────────────────────────────────
# Persisted as JSON so subscribers survive bot restarts.
# Note: Render resets the filesystem on redeploy, so users re-subscribe after redeployments.
SUBSCRIBERS_FILE = "subscribers.json"

def load_subscribers() -> set:
    try:
        with open(SUBSCRIBERS_FILE, "r") as f:
            data = json.load(f)
            subs = set(str(cid) for cid in data)
    except (FileNotFoundError, json.JSONDecodeError):
        subs = set()
    if OWNER_CHAT_ID:
        subs.add(str(OWNER_CHAT_ID))
    return subs

def save_subscribers(subs: set):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(list(subs), f)

subscribers: set = load_subscribers()


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def send_to_all(bot: Bot, messages: list):
    for chat_id in list(subscribers):
        try:
            for msg in messages:
                await bot.send_message(
                    chat_id=chat_id,
                    text=msg,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
        except Exception as e:
            logger.warning(f"Failed to send to {chat_id}: {e}")


# ─── Command Handlers ────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    already = chat_id in subscribers
    status_line = "You are already subscribed!" if already else "Use /subscribe to sign up for daily alerts."
    await update.message.reply_text(
        "*Aviation and PM Job Bot*\n\n"
        "Sends job listings 3x daily at 9:00 AM, 12:00 PM, and 3:00 PM SGT, "
        "covering aviation, admin, project management, data analysis, "
        "and airport counter roles — tailored for Air Transport Management graduates.\n\n"
        "*Commands:*\n"
        "/subscribe - Start receiving daily job updates\n"
        "/unsubscribe - Stop receiving daily updates\n"
        "/latest - Fetch the latest job listings now\n"
        "/status - Check if you are subscribed\n\n"
        + status_line,
        parse_mode="Markdown"
    )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in subscribers:
        await update.message.reply_text(
            "You are already subscribed!\n"
            "You will receive job updates at 9:00 AM, 12:00 PM, and 3:00 PM SGT daily."
        )
        return
    subscribers.add(chat_id)
    save_subscribers(subscribers)
    logger.info(f"New subscriber: {chat_id} (total: {len(subscribers)})")
    await update.message.reply_text(
        "*Subscribed!*\n\n"
        "You will now receive job listings at:\n"
        "- 9:00 AM SGT\n"
        "- 12:00 PM SGT\n"
        "- 3:00 PM SGT\n\n"
        "Use /latest to fetch jobs right now, or /unsubscribe to stop anytime.",
        parse_mode="Markdown"
    )

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id not in subscribers:
        await update.message.reply_text("You are not currently subscribed.")
        return
    subscribers.discard(chat_id)
    save_subscribers(subscribers)
    logger.info(f"Unsubscribed: {chat_id} (total: {len(subscribers)})")
    await update.message.reply_text(
        "Unsubscribed. You will not receive daily updates anymore.\n"
        "Use /subscribe anytime to start again."
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in subscribers:
        await update.message.reply_text(
            "You are subscribed and will receive job updates at "
            "9:00 AM, 12:00 PM, and 3:00 PM SGT daily."
        )
    else:
        await update.message.reply_text(
            "You are not subscribed. Use /subscribe to sign up."
        )

async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fetching latest jobs... this may take a moment.")
    try:
        jobs = await fetch_all_jobs()
        messages = format_jobs_message(jobs)
        for msg in messages:
            await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        await update.message.reply_text("Error fetching jobs. Please try again later.")


# ─── Scheduled Job ───────────────────────────────────────────────────────────

SCHEDULE_LABELS = {
    9:  "9:00 AM",
    12: "12:00 PM",
    15: "3:00 PM",
}

async def scheduled_job(bot: Bot, hour: int = 9):
    if not subscribers:
        logger.info("No subscribers, skipping scheduled fetch.")
        return
    label = SCHEDULE_LABELS.get(hour, f"{hour}:00")
    logger.info(f"[{label} SGT] Running scheduled job fetch for {len(subscribers)} subscriber(s)...")
    try:
        jobs = await fetch_all_jobs()
        messages = format_jobs_message(jobs, schedule_label=label)
        await send_to_all(bot, messages)
        logger.info(f"[{label} SGT] Scheduled push complete.")
    except Exception as e:
        logger.error(f"Scheduled job error: {e}")


# ─── Main ────────────────────────────────────────────────────────────────────

async def post_init(application: Application):
    """Runs once after the bot starts — registers the command menu with Telegram."""
    await application.bot.set_my_commands(BOT_COMMANDS)
    logger.info("Bot command menu registered.")

def main():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start",       start))
    app.add_handler(CommandHandler("subscribe",   subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(CommandHandler("status",      status))
    app.add_handler(CommandHandler("latest",      latest))

    scheduler = AsyncIOScheduler(timezone=SGT)
    for hour in [9, 12, 15]:
        scheduler.add_job(
            scheduled_job,
            CronTrigger(hour=hour, minute=0, timezone=SGT),
            args=[app.bot, hour]
        )
    scheduler.start()
    logger.info(f"Bot started. {len(subscribers)} subscriber(s) loaded. Scheduler running (9AM, 12PM, 3PM SGT).")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
