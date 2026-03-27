import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.services.polling_service import run_polling_cycle

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def init_scheduler():
    """Inicializa o scheduler com job de polling a cada 24 horas."""
    scheduler.add_job(
        run_polling_cycle,
        trigger=IntervalTrigger(hours=24),
        id="polling_cycle",
        name="SerpAPI polling cycle",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started with 24-hour polling interval")


def shutdown_scheduler():
    """Para o scheduler de forma limpa."""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
