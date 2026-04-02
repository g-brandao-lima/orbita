import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.polling_service import run_polling_cycle

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def init_scheduler():
    """Inicializa o scheduler com 2 jobs de polling diários.

    04:00 BRT (07:00 UTC): madrugada, quando companhias atualizam tarifas
    16:00 BRT (19:00 UTC): tarde, apos ajustes do dia
    """
    scheduler.add_job(
        run_polling_cycle,
        trigger=CronTrigger(hour=7, minute=0),  # 07:00 UTC = 04:00 BRT
        id="polling_morning",
        name="Polling matinal (04:00 BRT)",
        replace_existing=True,
    )
    scheduler.add_job(
        run_polling_cycle,
        trigger=CronTrigger(hour=19, minute=0),  # 19:00 UTC = 16:00 BRT
        id="polling_afternoon",
        name="Polling vespertino (16:00 BRT)",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started: daily polling at 04:00 and 16:00 BRT")


def shutdown_scheduler():
    """Para o scheduler de forma limpa."""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
