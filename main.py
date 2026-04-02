from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings.from_env()
    configure_logging(settings.log_level)

    db = Database(settings)
    db.init_schema()

    notifier = TelegramNotifier(settings)
    monitor = WhaleMonitor(db=db, notifier=notifier, settings=settings)
    sync_engine = WhaleSyncEngine(
        db=db, settings=settings, on_sync_success=monitor.request_reload
    )

    await monitor.load_addresses()
    await sync_engine.start()
    try:
        await sync_engine.sync_if_needed(force=False)
    except Exception:
        logging.getLogger(__name__).exception(
            "Initial Dune sync failed during startup. The API will continue running and retry on schedule."
        )

    # Start monitor as a background task
    monitor_task = asyncio.create_task(monitor.run())

    app.state.db = db
    app.state.monitor = monitor
    app.state.sync_engine = sync_engine
    app.state.notifier = notifier

    yield

    # Shutdown
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass
    await sync_engine.shutdown()
    await notifier.close()


app = FastAPI(title="Whale-Eye API", lifespan=lifespan)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/stats")
async def get_stats():
    return await asyncio.to_thread(app.state.db.get_stats)


CEX_MAP = {
    "0x28c6c06290d514ddd8897310521de05a3918a4b3": "Binance: Hot Wallet",
    "0x56eddb7aa87536c09ccc2793473599fd21a8b17f": "Binance: Wallet",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance: Wallet 2",
    "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be": "Binance: Cold Wallet",
}

@app.get("/api/whales")
async def get_whales(page: int = 1, size: int = 10):
    offset = (page - 1) * size
    data = await asyncio.to_thread(app.state.db.get_top_whales, size, offset)
    total = await asyncio.to_thread(app.state.db.get_whales_count)
    
    # Fallback enrich with entity_label when Dune did not provide one.
    for whale in data:
        addr = whale["address"].lower()
        if whale.get("entity_label"):
            continue
        if addr in CEX_MAP:
            whale["entity_label"] = CEX_MAP[addr]
        else:
            whale["entity_label"] = "Mega Whale"
            
    return {"data": data, "total": total, "page": page, "size": size}


@app.get("/api/alerts")
async def get_alerts(limit: int = 50):
    return await asyncio.to_thread(app.state.db.get_latest_alerts, limit)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
