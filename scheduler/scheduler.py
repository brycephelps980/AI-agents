import time
import schedule
from loguru import logger
from utils.config import get_config


class SchedulerService:
    def __init__(self, orchestrator) -> None:
        self.orchestrator = orchestrator

    def setup(self) -> None:
        cfg = get_config()
        run_time = cfg.schedule.overnight_run_time
        schedule.every().day.at(run_time).do(self._run_overnight)
        logger.info(f"Scheduled full pipeline at {run_time} daily")

        if cfg.schedule.midday_todo_reminder:
            midday = cfg.schedule.midday_run_time
            schedule.every().day.at(midday).do(self._run_midday)
            logger.info(f"Scheduled midday task reminder at {midday} daily")

    def _run_overnight(self) -> None:
        logger.info("Starting overnight full pipeline run")
        try:
            self.orchestrator.run_full_pipeline()
        except Exception as e:
            logger.error(f"Overnight run failed: {e}")

    def _run_midday(self) -> None:
        logger.info("Starting midday Present tier run")
        try:
            self.orchestrator.run_tier("present")
        except Exception as e:
            logger.error(f"Midday run failed: {e}")

    def run_forever(self) -> None:
        self.setup()
        logger.info("Scheduler daemon running — waiting for scheduled jobs...")
        while True:
            schedule.run_pending()
            time.sleep(30)
