from __future__ import annotations

import asyncio
import logging

from config import Settings
from database import Database
from monitor import WhaleMonitor
from notifier import TelegramNotifier
from sync_engine import WhaleSyncEngine


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


async def async_main() -> None:
    settings = Settings.from_env()
    configure_logging(settings.log_level)

    db = Database(settings)
    db.init_schema()

    notifier = TelegramNotifier(settings)
    monitor = WhaleMonitor(db=db, notifier=notifier, settings=settings)
    sync_engine = WhaleSyncEngine(db=db, settings=settings, on_sync_success=monitor.request_reload)

    await monitor.load_addresses()
    await sync_engine.start()
    await sync_engine.sync_if_needed(force=False)

    try:
        await monitor.run()
    finally:
        await sync_engine.shutdown()
        await notifier.close()


if __name__ == "__main__":
    asyncio.run(async_main())
