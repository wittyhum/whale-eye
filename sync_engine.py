from __future__ import annotations

import asyncio
import json
import logging
import time
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
    from dune_client.query import QueryBase
except ImportError:  # pragma: no cover
    DuneClient = None
    QueryBase = None


logger = logging.getLogger(__name__)
EXECUTION_POLL_INTERVAL_SECONDS = 5
EXECUTION_TIMEOUT_SECONDS = 300
SYNC_FRESHNESS_GRACE_SECONDS = 10
TERMINAL_STATES = {
    "QUERY_STATE_COMPLETED",
    "QUERY_STATE_COMPLETED_PARTIAL",
    "QUERY_STATE_FAILED",
    "QUERY_STATE_CANCELLED",
    "QUERY_STATE_EXPIRED",
}
SUCCESS_STATES = {
    "QUERY_STATE_COMPLETED",
    "QUERY_STATE_COMPLETED_PARTIAL",
}
FAILED_STATES = {
    "QUERY_STATE_FAILED",
    "QUERY_STATE_CANCELLED",
    "QUERY_STATE_EXPIRED",
}


class WhaleSyncEngine:
    JOB_ID = "dune_whale_sync"

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

        self.scheduler.start()
        await self._schedule_next_run()

    async def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    async def sync_if_needed(self, force: bool = False) -> bool:
        last_sync_at = await asyncio.to_thread(self.db.get_last_sync_at)
        if not force and last_sync_at is not None:
            now = datetime.now(timezone.utc)
            next_due_at = last_sync_at + timedelta(hours=self.settings.sync_interval_hours)
            if now + timedelta(seconds=SYNC_FRESHNESS_GRACE_SECONDS) < next_due_at:
                logger.info("Skip Dune sync because the last successful sync is still fresh.")
                await self._schedule_next_run(last_sync_at=last_sync_at)
                return False

        return await self.sync_once()

    async def sync_once(self) -> bool:
        rows = await asyncio.to_thread(self._fetch_whale_rows)
        row_count = await asyncio.to_thread(self.db.save_whale_list, rows)
        await asyncio.to_thread(self.db.record_sync_success, row_count)
        logger.info("Dune whale list synced successfully with %s active addresses.", row_count)

        if self.on_sync_success:
            await self.on_sync_success()
        await self._schedule_next_run()
        return True

    async def _resolve_next_run_time(self, last_sync_at: datetime | None = None) -> datetime:
        now = datetime.now(timezone.utc)
        if last_sync_at is None:
            last_sync_at = await asyncio.to_thread(self.db.get_last_sync_at)
        if last_sync_at is None:
            return now

        next_due_at = last_sync_at + timedelta(hours=self.settings.sync_interval_hours)
        if next_due_at <= now:
            return now
        return next_due_at

    async def _run_scheduled_sync(self) -> None:
        try:
            await self.sync_if_needed(force=False)
        finally:
            await self._schedule_next_run()

    async def _schedule_next_run(self, last_sync_at: datetime | None = None) -> None:
        if not self.scheduler.running:
            return

        next_run_time = await self._resolve_next_run_time(last_sync_at=last_sync_at)
        job = self.scheduler.get_job(self.JOB_ID)
        if job is None:
            self.scheduler.add_job(
                self._run_scheduled_sync,
                "date",
                run_date=next_run_time,
                id=self.JOB_ID,
                replace_existing=True,
            )
            logger.info("Scheduled next Dune sync at %s.", next_run_time.isoformat())
            return

        self.scheduler.modify_job(self.JOB_ID, next_run_time=next_run_time)
        logger.info("Rescheduled next Dune sync at %s.", next_run_time.isoformat())

    def _fetch_whale_rows(self) -> Sequence[Mapping[str, object]]:
        if DuneClient is not None and QueryBase is not None:
            try:
                client = DuneClient(api_key=self.settings.dune_api_key)
                result = self._execute_with_client(client)
                return self._extract_rows(result)
            except Exception as exc:  # pragma: no cover
                logger.warning("Dune client execution failed, falling back to HTTP API: %s", exc)

        return self._fetch_with_http_execution()

    def _execute_with_client(self, client: DuneClient) -> Any:
        query = QueryBase(query_id=self.settings.dune_query_id, name="whale-eye-sync")
        execution = client.execute(query)
        execution_id = execution.execution_id
        logger.info("Triggered Dune query execution %s for query %s.", execution_id, self.settings.dune_query_id)
        deadline = time.monotonic() + EXECUTION_TIMEOUT_SECONDS

        while True:
            status = client.get_execution_status(execution_id)
            state = self._state_value(status.state)
            if state in SUCCESS_STATES:
                result = client.get_execution_results(execution_id, allow_partial_results="true")
                return result
            if state in FAILED_STATES:
                error = getattr(status, "error", None)
                raise RuntimeError(
                    f"Dune query execution failed with state {state}. Error: {error}"
                )
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Dune query execution {execution_id} timed out after {EXECUTION_TIMEOUT_SECONDS} seconds."
                )
            time.sleep(EXECUTION_POLL_INTERVAL_SECONDS)

    def _fetch_with_http_execution(self) -> Sequence[Mapping[str, object]]:
        execution = self._request_json(
            url=f"https://api.dune.com/api/v1/query/{self.settings.dune_query_id}/execute",
            method="POST",
            payload={},
        )
        execution_id = execution.get("execution_id")
        if not execution_id:
            raise RuntimeError(f"Dune execute query did not return execution_id: {execution}")

        logger.info("Triggered Dune query execution %s for query %s.", execution_id, self.settings.dune_query_id)
        deadline = time.monotonic() + EXECUTION_TIMEOUT_SECONDS

        while True:
            status = self._request_json(
                url=f"https://api.dune.com/api/v1/execution/{execution_id}/status",
                method="GET",
            )
            state = str(status.get("state") or "").strip()
            if state in SUCCESS_STATES:
                result = self._request_json(
                    url=f"https://api.dune.com/api/v1/execution/{execution_id}/results?allow_partial_results=true",
                    method="GET",
                )
                rows = result.get("result", {}).get("rows", [])
                if not rows:
                    logger.warning("Dune execution result returned zero rows. Payload keys: %s", list(result.keys()))
                return [self._normalize_source_row(row) for row in rows]
            if state in FAILED_STATES:
                raise RuntimeError(
                    f"Dune query execution failed with state {state}. Payload: {status}"
                )
            if state not in TERMINAL_STATES and not state:
                raise RuntimeError(f"Dune execution status missing state. Payload: {status}")
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Dune query execution {execution_id} timed out after {EXECUTION_TIMEOUT_SECONDS} seconds."
                )
            time.sleep(EXECUTION_POLL_INTERVAL_SECONDS)

    def _request_json(self, url: str, method: str, payload: Mapping[str, object] | None = None) -> dict[str, Any]:
        headers = {
            "X-Dune-API-Key": self.settings.dune_api_key,
            "Accept": "application/json",
            "User-Agent": "whale-eye/1.0",
        }
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")

        request = Request(url=url, headers=headers, method=method, data=data)
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:  # pragma: no cover
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Failed to call Dune API: HTTP {exc.code} {exc.reason}. Response: {body}"
            ) from exc
        except URLError as exc:  # pragma: no cover
            raise RuntimeError(f"Failed to call Dune API: {exc}") from exc

    @staticmethod
    def _state_value(state: Any) -> str:
        if state is None:
            return ""
        return str(getattr(state, "value", state)).strip()

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
