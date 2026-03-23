import sys
from pathlib import Path

# Add project root to sys.path so we can run from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from jobs.daily_analysis import run_daily_analysis
from jobs.weight_updater import run_weight_update
from scripts.check_health import main as health_main

async def scheduled_analysis():
    logger.info("Starting scheduled daily MMCI analysis...")
    try:
        await run_daily_analysis()
        logger.info("Daily MMCI analysis completed successfully.")
    except Exception as e:
        logger.error(f"Daily analysis job failed: {e}")

async def scheduled_weight_update():
    logger.info("Starting scheduled T+5 weight update...")
    try:
        await run_weight_update()
        logger.info("T+5 weight update completed successfully.")
    except Exception as e:
        logger.error(f"Weight update job failed: {e}")

async def main():
    logger.info("Initializing Pantheon Autonomous Scheduler")
    
    # Validate system health before entering hibernation/scheduling
    logger.info("Running initial pre-flight health checks...")
    try:
        health_main()
    except Exception as e:
        logger.warning(f"Health checks raised an issue: {e}")
    
    scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
    
    # Daily Analysis at 16:00 IST (4:00 PM - After market close)
    scheduler.add_job(
        scheduled_analysis,
        trigger='cron',
        day_of_week='mon-fri',
        hour=16,
        minute=0,
        id='mmci_daily_analysis',
        replace_existing=True
    )
    
    # Weight Tuner at 16:30 IST (4:30 PM)
    scheduler.add_job(
        scheduled_weight_update,
        trigger='cron',
        day_of_week='mon-fri',
        hour=16,
        minute=30,
        id='mmci_weight_tuner',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler Active. Waiting for cron triggers (Ctrl+C to exit)...")
    
    try:
        while True:
            await asyncio.sleep(3600)
    except (asyncio.CancelledError, KeyboardInterrupt):
         logger.info("Shutting down Pantheon Scheduler natively.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
