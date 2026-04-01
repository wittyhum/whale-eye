from __future__ import annotations

import asyncio
import json
import logging
from decimal import Decimal
from typing import Any, Mapping, Sequence

import websockets

from config import Settings
from database import AlertRecord, Database
from notifier import TelegramNotifier


logger = logging.getLogger(__name__)
WEI_IN_ETH = Decimal("1000000000000000000")


class WhaleMonitor:
    def __init__(self, db: Database, notifier: TelegramNotifier, settings: Settings) -> None:
        self.db = db
        self.notifier = notifier
        self.settings = settings
        self._addresses: set[str] = set()
        self._address_lock = asyncio.Lock()
        self._resubscribe_event = asyncio.Event()

    async def load_addresses(self) -> None:
        addresses = await asyncio.to_thread(self.db.get_active_addresses)
        async with self._address_lock:
            self._addresses = set(addresses)
        logger.info("Loaded %s active whale addresses.", len(addresses))

    async def request_reload(self) -> None:
        await self.load_addresses()
        self._resubscribe_event.set()

    async def run(self) -> None:
        reconnect_delay = 1
        while True:
            try:
                await self.load_addresses()
                await self._run_connection()
                reconnect_delay = 1
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("Alchemy monitor disconnected: %s", exc)
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, self.settings.reconnect_max_seconds)

    async def _run_connection(self) -> None:
        async with websockets.connect(
            self.settings.alchemy_wss_url,
            ping_interval=20,
            ping_timeout=20,
            close_timeout=10,
            max_size=4 * 1024 * 1024,
        ) as websocket:
            await self._subscribe(websocket)
            logger.info("Alchemy websocket connected.")

            reload_task = asyncio.create_task(self._watch_reload(websocket))
            periodic_refresh_task = asyncio.create_task(self._periodic_refresh())

            try:
                async for message in websocket:
                    payload = json.loads(message)
                    await self._handle_message(payload)
            finally:
                reload_task.cancel()
                periodic_refresh_task.cancel()
                await asyncio.gather(reload_task, periodic_refresh_task, return_exceptions=True)

    async def _subscribe(self, websocket: websockets.WebSocketClientProtocol) -> None:
        addresses = await self._address_snapshot()
        if not addresses:
            logger.warning("No active whale addresses found. Waiting for the next refresh cycle.")
            return

        requests = self._build_subscription_requests(addresses)
        for request_payload in requests:
            await websocket.send(json.dumps(request_payload))

    def _build_subscription_requests(self, addresses: Sequence[str]) -> list[dict[str, object]]:
        filter_base = {
            "category": ["external"],
        }
        return [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": self.settings.alchemy_subscription_method,
                "params": [
                    self.settings.alchemy_subscription_type,
                    {**filter_base, "fromAddress": list(addresses)},
                ],
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": self.settings.alchemy_subscription_method,
                "params": [
                    self.settings.alchemy_subscription_type,
                    {**filter_base, "toAddress": list(addresses)},
                ],
            },
        ]

    async def _watch_reload(self, websocket: websockets.WebSocketClientProtocol) -> None:
        await self._resubscribe_event.wait()
        self._resubscribe_event.clear()
        await websocket.close()

    async def _periodic_refresh(self) -> None:
        while True:
            await asyncio.sleep(self.settings.address_refresh_seconds)
            previous = await self._address_snapshot()
            await self.load_addresses()
            current = await self._address_snapshot()
            if current != previous:
                logger.info("Whale address set changed. Re-subscribing websocket filters.")
                self._resubscribe_event.set()
                return

    async def _handle_message(self, payload: Mapping[str, Any]) -> None:
        transfer = self._extract_transfer(payload)
        if transfer is None:
            return

        from_addr = str(transfer.get("from", "")).lower()
        to_addr = str(transfer.get("to", "")).lower()
        tx_hash = str(transfer.get("hash") or transfer.get("transactionHash") or "").lower()
        if not tx_hash or not from_addr or not to_addr:
            return

        addresses = await self._address_snapshot()
        if from_addr not in addresses and to_addr not in addresses:
            return

        eth_value = self._extract_eth_value(transfer)
        if eth_value < self.settings.eth_threshold:
            return

        direction = self._detect_direction(from_addr, to_addr, addresses)
        alert = AlertRecord(
            tx_hash=tx_hash,
            from_addr=from_addr,
            to_addr=to_addr,
            eth_value=eth_value,
            direction=direction,
        )
        inserted = await asyncio.to_thread(self.db.save_alert, alert)
        if not inserted:
            return

        await self.notifier.send_alert(
            alert,
            from_label=self.settings.known_exchanges.get(from_addr),
            to_label=self.settings.known_exchanges.get(to_addr),
        )
        logger.info("Alert pushed for tx %s (%s ETH).", tx_hash, eth_value)

    async def _address_snapshot(self) -> set[str]:
        async with self._address_lock:
            return set(self._addresses)

    def _detect_direction(self, from_addr: str, to_addr: str, monitored_addresses: set[str]) -> str:
        known_exchanges = self.settings.known_exchanges
        if from_addr in known_exchanges and to_addr in monitored_addresses:
            return "Withdrawal"
        if from_addr in monitored_addresses and to_addr in known_exchanges:
            return "Deposit"
        return "Transfer"

    @staticmethod
    def _extract_transfer(payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
        if "params" in payload and isinstance(payload["params"], Mapping):
            result = payload["params"].get("result")
            if isinstance(result, Mapping):
                if "transaction" in result and isinstance(result["transaction"], Mapping):
                    return result["transaction"]
                return result

        result = payload.get("result")
        if isinstance(result, Mapping):
            if "transaction" in result and isinstance(result["transaction"], Mapping):
                return result["transaction"]
            return result
        return None

    @staticmethod
    def _extract_eth_value(transfer: Mapping[str, Any]) -> Decimal:
        raw_value = transfer.get("value")
        if raw_value not in (None, ""):
            if isinstance(raw_value, str) and raw_value.startswith("0x"):
                return Decimal(int(raw_value, 16)) / WEI_IN_ETH
            return Decimal(str(raw_value))

        raw_contract = transfer.get("rawContract")
        if isinstance(raw_contract, Mapping):
            contract_value = raw_contract.get("value")
            if isinstance(contract_value, str) and contract_value:
                if contract_value.startswith("0x"):
                    return Decimal(int(contract_value, 16)) / WEI_IN_ETH
                return Decimal(contract_value)

        metadata = transfer.get("metadata")
        if isinstance(metadata, Mapping) and metadata.get("value") is not None:
            return Decimal(str(metadata["value"]))

        return Decimal("0")
