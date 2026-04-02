from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Awaitable, Callable, Iterable, List, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import Settings
from database import Database

try:
    from dune_client.client import DuneClient
except ImportError:  # pragma: no cover
    DuneClient = None


logger = logging.getLogger(__name__)


class WhaleSyncEngine:
    def __init__(
        self,
        db: Database,
        settings: Settings,
        on_sync_success: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        self.db = db
        self.settings = settings
        self.on_sync_success = on_sync_success
        self.scheduler = AsyncIOScheduler(timezone=timezone.utc)

    async def start(self) -> None:
        if self.scheduler.running:
            return

        self.scheduler.add_job(
            self.sync_if_needed,
            "interval",
            hours=self.settings.sync_interval_hours,
            id="dune_whale_sync",
            max_instances=1,
            coalesce=True,
        )
        self.scheduler.start()

    async def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    async def sync_if_needed(self, force: bool = False) -> bool:
        last_sync_at = await asyncio.to_thread(self.db.get_last_sync_at)
        if not force and last_sync_at is not None:
            now = datetime.now(timezone.utc)
            if now - last_sync_at < timedelta(hours=self.settings.sync_interval_hours):
                logger.info("Skip Dune sync because the last successful sync is still fresh.")
                return False

        return await self.sync_once()

    async def sync_once(self) -> bool:
        rows = await asyncio.to_thread(self._fetch_whale_rows)
        row_count = await asyncio.to_thread(self.db.save_whale_list, rows)
        await asyncio.to_thread(self.db.record_sync_success, row_count)
        logger.info("Dune whale list synced successfully with %s active addresses.", row_count)

        if self.on_sync_success:
            await self.on_sync_success()
        return True

    def _fetch_whale_rows(self) -> Sequence[Mapping[str, object]]:
        if DuneClient is not None:
            try:
                client = DuneClient(api_key=self.settings.dune_api_key)
                if hasattr(client, "get_latest_result"):
                    result = client.get_latest_result(self.settings.dune_query_id)
                else:
                    result = client.run_query(self.settings.dune_query_id)
                return self._extract_rows(result)
            except Exception as exc:  # pragma: no cover
                logger.warning("Dune client fetch failed, falling back to HTTP API: %s", exc)

        return self._fetch_with_http()

    def _fetch_with_http(self) -> Sequence[Mapping[str, object]]:
        request = Request(
            url=(
                f"https://api.dune.com/api/v1/query/{self.settings.dune_query_id}/results"
                "?allow_partial_results=true"
            ),
            headers={
                "X-Dune-API-Key": self.settings.dune_api_key,
                "Accept": "application/json",
                "User-Agent": "whale-eye/1.0",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:  # pragma: no cover
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Failed to fetch Dune query result: HTTP {exc.code} {exc.reason}. Response: {body}"
            ) from exc
        except URLError as exc:  # pragma: no cover
            raise RuntimeError(f"Failed to fetch Dune query result: {exc}") from exc

        rows = payload.get("result", {}).get("rows", [])
        error = payload.get("error")
        state = payload.get("state")
        if error:
            raise RuntimeError(f"Dune query returned an error: {error}")
        if state and state not in {"QUERY_STATE_COMPLETED", "QUERY_STATE_COMPLETED_PARTIAL"}:
            raise RuntimeError(f"Dune query is not ready yet. Current state: {state}")
        if not rows:
            logger.warning("Dune latest result returned zero rows. Payload keys: %s", list(payload.keys()))
        return [self._normalize_source_row(row) for row in rows]

    def _extract_rows(self, result: Any) -> Sequence[Mapping[str, object]]:
        if result is None:
            return []

        if hasattr(result, "to_dict"):
            try:
                rows = result.to_dict("records")
                return [self._normalize_source_row(row) for row in rows]
            except TypeError:
                pass

        if isinstance(result, dict):
            rows = result.get("result", {}).get("rows") or result.get("rows") or []
            return [self._normalize_source_row(row) for row in rows]

        if hasattr(result, "result") and hasattr(result.result, "rows"):
            return [self._normalize_source_row(row) for row in result.result.rows]

        if hasattr(result, "rows"):
            return [self._normalize_source_row(row) for row in result.rows]

        if isinstance(result, list):
            return [self._normalize_source_row(row) for row in result]

        raise RuntimeError("Unsupported Dune query result format.")

    @staticmethod
    def _normalize_source_row(row: Mapping[str, Any]) -> Mapping[str, object]:
        key_map = {str(key).lower(): value for key, value in row.items()}
        address = (
            key_map.get("address")
            or key_map.get("wallet_address")
            or key_map.get("user_address")
            or key_map.get("from_address")
        )
        if not address:
            raise ValueError(f"Dune row does not contain an address field: {row}")

        return {
            "address": str(address).lower(),
            "total_eth_in": Decimal(str(key_map.get("total_eth_in", key_map.get("eth_in", "0")) or "0")),
            "total_eth_out": Decimal(str(key_map.get("total_eth_out", key_map.get("eth_out", "0")) or "0")),
            "net_flow": Decimal(str(key_map.get("net_flow", "0") or "0")),
            "in_tx_count": int(key_map.get("in_tx_count", 0) or 0),
            "out_tx_count": int(key_map.get("out_tx_count", 0) or 0),
            "tx_count": int(key_map.get("tx_count", key_map.get("count", 0)) or 0),
            "last_active_time": key_map.get("last_active_time") or key_map.get("last_tx_at"),
            "entity_label": key_map.get("entity_label"),
        }
