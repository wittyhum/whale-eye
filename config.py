from __future__ import annotations

import json
import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Dict

from dotenv import load_dotenv


load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Environment variable {name} is required.")
    return value


def _decimal_env(name: str, default: str) -> Decimal:
    raw_value = os.getenv(name, default).strip()
    try:
        return Decimal(raw_value)
    except InvalidOperation as exc:
        raise ValueError(f"Environment variable {name} must be a valid decimal.") from exc


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer.") from exc


def _load_exchange_mapping() -> Dict[str, str]:
    raw_value = os.getenv("KNOWN_EXCHANGES_JSON", "{}").strip()
    if not raw_value:
        return {}

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ValueError("KNOWN_EXCHANGES_JSON must be a valid JSON object.") from exc

    if not isinstance(parsed, dict):
        raise ValueError("KNOWN_EXCHANGES_JSON must decode to a JSON object.")

    return {str(address).lower(): str(name) for address, name in parsed.items()}


@dataclass(frozen=True)
class Settings:
    dune_api_key: str
    dune_query_id: int
    alchemy_wss_url: str
    alchemy_http_url: str
    alchemy_subscription_method: str
    alchemy_subscription_type: str
    tg_bot_token: str
    tg_chat_id: str
    tg_proxy: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    db_pool_size: int
    eth_threshold: Decimal
    sync_interval_hours: int
    address_refresh_seconds: int
    reconnect_max_seconds: int
    log_level: str
    known_exchanges: Dict[str, str]

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            dune_api_key=_require_env("DUNE_API_KEY"),
            dune_query_id=_int_env("DUNE_QUERY_ID", 0),
            alchemy_wss_url=_require_env("ALCHEMY_WSS_URL"),
            alchemy_http_url=os.getenv("ALCHEMY_HTTP_URL", "").strip(),
            alchemy_subscription_method=os.getenv("ALCHEMY_SUBSCRIPTION_METHOD", "alchemy_subscribe").strip(),
            alchemy_subscription_type=os.getenv("ALCHEMY_SUBSCRIPTION_TYPE", "alchemy_filteredTransfers").strip(),
            tg_bot_token=_require_env("TG_BOT_TOKEN"),
            tg_chat_id=_require_env("TG_CHAT_ID"),
            tg_proxy=os.getenv("TG_PROXY", "").strip(),
            db_host=os.getenv("DB_HOST", "localhost").strip(),
            db_port=_int_env("DB_PORT", 3306),
            db_user=os.getenv("DB_USER", "root").strip(),
            db_password=os.getenv("DB_PASSWORD", "123456"),
            db_name=os.getenv("DB_NAME", "whale_eye").strip(),
            db_pool_size=_int_env("DB_POOL_SIZE", 5),
            eth_threshold=_decimal_env("ETH_THRESHOLD", "500"),
            sync_interval_hours=_int_env("SYNC_INTERVAL_HOURS", 12),
            address_refresh_seconds=_int_env("ADDRESS_REFRESH_SECONDS", 300),
            reconnect_max_seconds=_int_env("RECONNECT_MAX_SECONDS", 60),
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
            known_exchanges=_load_exchange_mapping(),
        )
