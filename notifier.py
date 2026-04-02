from __future__ import annotations

import html
from decimal import Decimal

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from config import Settings
from database import AlertRecord


class TelegramNotifier:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        session = AiohttpSession(proxy=settings.tg_proxy) if settings.tg_proxy else None
        self.bot = Bot(token=settings.tg_bot_token, session=session)

    async def send_alert(
        self,
        alert: AlertRecord,
        from_label: str | None = None,
        to_label: str | None = None,
    ) -> None:
        direction_icons = {
            "Withdrawal": "🏦",
            "Deposit": "🏦",
            "Transfer": "🚨",
            "BuyETH": "🟢",
            "SellETH": "🔴",
        }
        direction_icon = direction_icons.get(alert.direction, "🚨")
        direction_text = {
            "Withdrawal": "Exchange Withdrawal",
            "Deposit": "Exchange Deposit",
            "Transfer": "Large Transfer",
            "BuyETH": "Whale Bought ETH",
            "SellETH": "Whale Sold ETH",
        }.get(alert.direction, alert.direction)
        message = (
            f"{direction_icon} <b>{html.escape(direction_text)}</b>\n"
            f"Amount: <b>{self._format_decimal(alert.eth_value)} ETH</b>\n"
            f"From: <code>{html.escape(self._address_label(alert.from_addr, from_label))}</code>\n"
            f"To: <code>{html.escape(self._address_label(alert.to_addr, to_label))}</code>\n"
            f"Tx: <a href=\"https://etherscan.io/tx/{html.escape(alert.tx_hash)}\">"
            f"{html.escape(self._short_hash(alert.tx_hash))}</a>"
        )
        await self.bot.send_message(
            chat_id=self.settings.tg_chat_id,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

    async def close(self) -> None:
        await self.bot.session.close()

    @staticmethod
    def _short_hash(tx_hash: str) -> str:
        return f"{tx_hash[:10]}...{tx_hash[-8:]}"

    @staticmethod
    def _format_decimal(value: Decimal) -> str:
        normalized = value.quantize(Decimal("0.00000001"))
        return format(normalized.normalize(), "f")

    @staticmethod
    def _address_label(address: str, label: str | None) -> str:
        short_address = f"{address[:8]}...{address[-6:]}"
        if label:
            return f"{label} ({short_address})"
        return short_address
