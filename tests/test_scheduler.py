from unittest.mock import patch, MagicMock


class TestSchedulerSetup:
    """Tests for scheduler initialization and shutdown."""

    @patch("app.scheduler.BackgroundScheduler")
    def test_scheduler_registers_daily_cron_job(self, mock_scheduler_cls):
        from app.scheduler import init_scheduler

        mock_sched_instance = MagicMock()
        mock_scheduler_cls.return_value = mock_sched_instance

        import app.scheduler as sched_module

        sched_module.scheduler = mock_sched_instance

        init_scheduler()

        mock_sched_instance.add_job.assert_called_once()

        call_kwargs = mock_sched_instance.add_job.call_args
        assert call_kwargs.kwargs.get("id") == "polling_cycle" or (
            len(call_kwargs.args) > 0
            and call_kwargs[1].get("id") == "polling_cycle"
        )

        # Check trigger is CronTrigger at 07:00 UTC (04:00 BRT)
        trigger = call_kwargs.kwargs.get("trigger") or call_kwargs.args[1]
        from apscheduler.triggers.cron import CronTrigger

        assert isinstance(trigger, CronTrigger)

        mock_sched_instance.start.assert_called_once()

    @patch("app.scheduler.BackgroundScheduler")
    def test_scheduler_shutdown_stops_cleanly(self, mock_scheduler_cls):
        from app.scheduler import shutdown_scheduler

        mock_sched_instance = MagicMock()
        mock_scheduler_cls.return_value = mock_sched_instance

        import app.scheduler as sched_module

        sched_module.scheduler = mock_sched_instance

        shutdown_scheduler()

        mock_sched_instance.shutdown.assert_called_once()
