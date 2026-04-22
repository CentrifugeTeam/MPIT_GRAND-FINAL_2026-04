import asyncio

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.core.queues import QUEUE_REPORT_TASK_INCOMING
from app.services.rabbitmq_publish import rabbit_publish
from app.services.run_store import create_run
from app.services.task_store import reserve_due_tasks

_scheduler: BackgroundScheduler | None = None


def dispatch_due_report_runs() -> None:
    rows = reserve_due_tasks(limit=100)
    if not rows:
        return

    async def _publish_all() -> None:
        for row in rows:
            run = create_run(row["task_id"], row["user_id"], row["instruction"])
            payload = {
                "report_id": run["id"],
                "task_id": row["task_id"],
                "user_id": row["user_id"],
                "conversation_id": "__report_run__",
                "message_id": f"report-run-{run['id']}",
                "content": row["instruction"],
                "analytics_source_key": row["analytics_source_key"],
                "scheduled_report": True,
            }
            try:
                await rabbit_publish.publish_json(QUEUE_REPORT_TASK_INCOMING, payload)
            except Exception:
                continue

    asyncio.run(_publish_all())


def start_scheduler() -> None:
    global _scheduler
    if _scheduler:
        return
    s = get_settings()
    interval = max(15, int(s.DISPATCH_INTERVAL_SECONDS))
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        dispatch_due_report_runs,
        "interval",
        seconds=interval,
        id="report_dispatch",
        replace_existing=True,
    )
    _scheduler.start()


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
