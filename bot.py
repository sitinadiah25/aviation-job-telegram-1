import os
import logging
import asyncio
from datetime import time
from telegram import Update, Bot
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
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SGT = pytz.timezone("Asia/Singapore")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✈️ *Aviation & PM Job Bot*\n\n"
        "I'll send you relevant job listings every day at *9:00 AM SGT*.\n\n"
        "Commands:\n"
        "/latest — Fetch the latest job listings now\n"
        "/start — Show this message\n\n"
        "Jobs are sourced from MyCareersFuture, LinkedIn, Indeed, and aviation company career portals.",
        parse_mode="Markdown"
    )

async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Fetching latest jobs... this may take a moment.")
    try:
        jobs = await fetch_all_jobs()
        messages = format_jobs_message(jobs)
        for msg in messages:
            await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        await update.message.reply_text("❌ Error fetching jobs. Please try again later.")

async def scheduled_job(bot: Bot):
    logger.info("Running scheduled job fetch...")
    try:
        jobs = await fetch_all_jobs()
        messages = format_jobs_message(jobs)
        for msg in messages:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=msg,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
    except Exception as e:
        logger.error(f"Scheduled job error: {e}")

def main():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    if not CHAT_ID:
        raise ValueError("TELEGRAM_CHAT_ID environment variable not set")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("latest", latest))

    scheduler = AsyncIOScheduler(timezone=SGT)
    scheduler.add_job(
        scheduled_job,
        CronTrigger(hour=9, minute=0, timezone=SGT),
        args=[app.bot]
    )
    scheduler.start()
    logger.info("Scheduler started. Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
