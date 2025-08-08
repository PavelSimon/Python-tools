from apscheduler.schedulers.blocking import BlockingScheduler
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_all_tasks():
    try:
        logger.info("Starting automation tasks...")
        # Example automation tasks - replace with your actual tasks
        logger.info("Task 1: Checking system status")
        logger.info("Task 2: Cleaning temporary files")
        logger.info("Task 3: Backing up important data")
        logger.info("All automation tasks completed successfully")
    except Exception as e:
        logger.error(f"Error running automation tasks: {e}")

# Setup scheduler
scheduler = BlockingScheduler()
scheduler.add_job(run_all_tasks, "interval", days=1)

logger.info("Starting daily automation scheduler...")
logger.info("Press Ctrl+C to stop")

try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    logger.info("Shutting down scheduler...")
    scheduler.shutdown()
    logger.info("Scheduler stopped")
