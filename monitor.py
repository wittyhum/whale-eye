from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping, Sequence

import websockets
from web3 import Web3

from config import Settings
from database import AlertRecord, Database
from notifier import TelegramNotifier


logger = logging.getLogger(__name__)
WEI_IN_ETH = Decimal("1000000000000000000")
TRANSFER_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex().lower()
WETH_ADDRESS = "0xc02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2".lower()
TOKEN_METADATA = {
    WETH_ADDRESS: {"symbol": "WETH", "decimals": 18},
    "0xdac17f958d2ee523a2206206994597c13d831ec7": {"symbol": "USDT", "decimals": 6},
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {"symbol": "USDC", "decimals": 6},
    "0x6b175474e89094c44da98b954eedeac495271d0f": {"symbol": "DAI", "decimals": 18},
    "0x4c9edd5852cd905f086c759e8383e09bff1e68b3": {"symbol": "USDe", "decimals": 18},
    "0xdc035d45d973e3ec169d2276ddab16f1e407384f": {"symbol": "USDS", "decimals": 18},
    "0x0000000000085d4780b73119b644ae5ecd22b376": {"symbol": "TUSD", "decimals": 18},
    "0x853d955acef822db058eb8505911ed77f175b99e": {"symbol": "FRAX", "decimals": 18},
    "0x5f98805a4e8be255a32880fdec7f6728c6568ba0": {"symbol": "LUSD", "decimals": 18},
    "0x6c3ea9036406852006290770bedfcaba0e23a0e8": {"symbol": "PYUSD", "decimals": 6},
}
STABLECOIN_ADDRESSES = {
    address
    for address, meta in TOKEN_METADATA.items()
    if meta["symbol"] in {"USDT", "USDC", "DAI", "USDe", "USDS", "TUSD", "FRAX", "LUSD", "PYUSD"}
}


@dataclass(frozen=True)
class SemanticSignal:
    direction: str
    eth_value: Decimal


class WhaleMonitor:
    def __init__(self, db: Database, notifier: TelegramNotifier, settings: Settings) -> None:
        self.db = db
        self.notifier = notifier
        self.settings = settings
        self._addresses: set[str] = set()
        self._address_lock = asyncio.Lock()
        self._resubscribe_event = asyncio.Event()
        self._last_ping_ms: int | None = None
        self.web3 = Web3(Web3.HTTPProvider(self._alchemy_http_url(settings), request_kwargs={"timeout": 30}))

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
            ping_task = asyncio.create_task(self._ping_loop(websocket))

            try:
                async for message in websocket:
                    payload = json.loads(message)
                    await self._handle_message(payload)
            finally:
                reload_task.cancel()
                periodic_refresh_task.cancel()
                ping_task.cancel()
                await asyncio.gather(
                    reload_task, periodic_refresh_task, ping_task, return_exceptions=True
                )

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
            "category": ["external", "erc20"],
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

    async def _ping_loop(self, websocket: websockets.WebSocketClientProtocol) -> None:
        while True:
            await asyncio.sleep(10)
            started_at = time.perf_counter()
            pong_waiter = await websocket.ping()
            await pong_waiter
            self._last_ping_ms = max(1, int((time.perf_counter() - started_at) * 1000))

    def get_last_ping_ms(self) -> int | None:
        return self._last_ping_ms

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

        transfer_eth_value = self._extract_eth_value(transfer)
        semantic_signal = await asyncio.to_thread(
            self._classify_transaction_semantics,
            tx_hash,
            from_addr,
            to_addr,
            addresses,
            transfer_eth_value,
        )
        if semantic_signal is not None:
            eth_value = semantic_signal.eth_value
            direction = semantic_signal.direction
        else:
            eth_value = transfer_eth_value
            direction = self._detect_direction(from_addr, to_addr, addresses)

        if eth_value < self.settings.record_threshold_eth:
            return

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

        if self._should_push_telegram(alert):
            await self.notifier.send_alert(
                alert,
                from_label=self.settings.known_exchanges.get(from_addr),
                to_label=self.settings.known_exchanges.get(to_addr),
            )
            logger.info("Alert pushed for tx %s (%s ETH).", tx_hash, eth_value)
        else:
            logger.info("Alert recorded without Telegram push for tx %s (%s ETH).", tx_hash, eth_value)

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

    def _should_push_telegram(self, alert: AlertRecord) -> bool:
        threshold = self._telegram_threshold(alert.direction)
        return alert.eth_value >= threshold

    def _telegram_threshold(self, direction: str) -> Decimal:
        if direction in {"BuyETH", "SellETH"}:
            return self.settings.telegram_buy_sell_threshold_eth
        if direction in {"Deposit", "Withdrawal"}:
            return self.settings.telegram_exchange_flow_threshold_eth
        return self.settings.telegram_transfer_threshold_eth

    def _classify_transaction_semantics(
        self,
        tx_hash: str,
        from_addr: str,
        to_addr: str,
        monitored_addresses: set[str],
        transfer_eth_value: Decimal,
    ) -> SemanticSignal | None:
        if from_addr in self.settings.known_exchanges and to_addr in monitored_addresses:
            return None
        if from_addr in monitored_addresses and to_addr in self.settings.known_exchanges:
            return None

        try:
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)
        except Exception as exc:
            logger.debug("Failed to fetch transaction receipt for %s: %s", tx_hash, exc)
            return None

        token_transfers = self._extract_token_transfers(receipt)
        if not token_transfers:
            return None

        whale_address = from_addr if from_addr in monitored_addresses else to_addr
        weth_in = Decimal("0")
        weth_out = Decimal("0")
        stable_in = Decimal("0")
        stable_out = Decimal("0")

        for transfer in token_transfers:
            token = transfer["token"]
            amount = transfer["amount"]
            sender = transfer["from"]
            recipient = transfer["to"]

            if sender == whale_address:
                if token == WETH_ADDRESS:
                    weth_out += amount
                if token in STABLECOIN_ADDRESSES:
                    stable_out += amount

            if recipient == whale_address:
                if token == WETH_ADDRESS:
                    weth_in += amount
                if token in STABLECOIN_ADDRESSES:
                    stable_in += amount

        if stable_out > 0 and weth_in >= self.settings.record_threshold_eth:
            return SemanticSignal(direction="BuyETH", eth_value=weth_in)

        if weth_out >= self.settings.record_threshold_eth and stable_in > 0:
            return SemanticSignal(direction="SellETH", eth_value=weth_out)

        if (
            transfer_eth_value >= self.settings.record_threshold_eth
            and to_addr in monitored_addresses
            and stable_out > 0
        ):
            return SemanticSignal(direction="BuyETH", eth_value=transfer_eth_value)

        if (
            transfer_eth_value >= self.settings.record_threshold_eth
            and from_addr in monitored_addresses
            and stable_in > 0
        ):
            return SemanticSignal(direction="SellETH", eth_value=transfer_eth_value)

        return None

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
    def _alchemy_http_url(settings: Settings) -> str:
        if settings.alchemy_http_url:
            return settings.alchemy_http_url
        if settings.alchemy_wss_url.startswith("wss://"):
            return "https://" + settings.alchemy_wss_url[len("wss://") :]
        if settings.alchemy_wss_url.startswith("ws://"):
            return "http://" + settings.alchemy_wss_url[len("ws://") :]
        return settings.alchemy_wss_url

    @staticmethod
    def _extract_address_from_topic(topic: str) -> str:
        normalized = topic.lower()
        if normalized.startswith("0x"):
            normalized = normalized[2:]
        return "0x" + normalized[-40:]

    @staticmethod
    def _token_amount(raw_value: str, decimals: int) -> Decimal:
        if not raw_value:
            return Decimal("0")
        value_int = int(raw_value, 16) if raw_value.startswith("0x") else int(raw_value)
        return Decimal(value_int) / (Decimal(10) ** decimals)

    def _extract_token_transfers(self, receipt: Mapping[str, Any]) -> list[dict[str, Any]]:
        logs = receipt.get("logs", [])
        transfers: list[dict[str, Any]] = []
        for log in logs:
            if not isinstance(log, Mapping):
                continue
            topics = log.get("topics") or []
            if len(topics) < 3:
                continue
            topic0 = topics[0]
            if isinstance(topic0, bytes):
                topic0 = topic0.hex()
            topic0 = str(topic0).lower()
            if topic0 != TRANSFER_TOPIC:
                continue

            token_address = str(log.get("address", "")).lower()
            metadata = TOKEN_METADATA.get(token_address)
            if metadata is None:
                continue

            sender_topic = topics[1]
            recipient_topic = topics[2]
            if isinstance(sender_topic, bytes):
                sender_topic = sender_topic.hex()
            if isinstance(recipient_topic, bytes):
                recipient_topic = recipient_topic.hex()

            transfers.append(
                {
                    "token": token_address,
                    "from": self._extract_address_from_topic(str(sender_topic)),
                    "to": self._extract_address_from_topic(str(recipient_topic)),
                    "amount": self._token_amount(str(log.get("data", "0x0")), int(metadata["decimals"])),
                }
            )
        return transfers

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
