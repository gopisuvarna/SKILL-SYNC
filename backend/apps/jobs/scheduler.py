"""APScheduler: run job sync on startup and every 24 hours."""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)
_scheduler = None


def run_job_sync():
    try:
        from apps.jobs.services import sync_jobs
        sync_jobs(country='us', max_pages=2)
    except Exception as e:
        logger.exception("Job sync failed: %s", e)


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(run_job_sync, IntervalTrigger(hours=24), id='job_sync')
    _scheduler.start()
    run_job_sync()
    logger.info("Job scheduler started")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
