import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.polling_service import run_polling_cycle

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def init_scheduler():
    """Inicializa o scheduler com job de polling diário às 07:00 UTC (04:00 BRT)."""
    scheduler.add_job(
        run_polling_cycle,
        trigger=CronTrigger(hour=7, minute=0),  # 07:00 UTC = 04:00 BRT
        id="polling_cycle",
        name="SerpAPI polling cycle",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started: daily polling at 04:00 BRT (07:00 UTC)")


def shutdown_scheduler():
    """Para o scheduler de forma limpa."""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
