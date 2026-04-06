from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Mapping, Sequence

import mysql.connector
from mysql.connector import pooling

from config import Settings


@dataclass(frozen=True)
class AlertRecord:
    tx_hash: str
    from_addr: str
    to_addr: str
    eth_value: Decimal
    direction: str


class Database:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._ensure_database_exists()
        self.pool = pooling.MySQLConnectionPool(
            pool_name="whale_eye_pool",
            pool_size=settings.db_pool_size,
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            autocommit=False,
        )

    def _ensure_database_exists(self) -> None:
        connection = mysql.connector.connect(
            host=self.settings.db_host,
            port=self.settings.db_port,
            user=self.settings.db_user,
            password=self.settings.db_password,
            autocommit=True,
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{self.settings.db_name}` CHARACTER SET utf8mb4"
                )
        finally:
            connection.close()

    def _get_connection(self) -> mysql.connector.MySQLConnection:
        return self.pool.get_connection()

    def init_schema(self) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS whales (
                address VARCHAR(42) PRIMARY KEY,
                total_eth_in DECIMAL(36, 18) DEFAULT 0,
                total_eth_out DECIMAL(36, 18),
                net_flow DECIMAL(36, 18) DEFAULT 0,
                in_tx_count INT DEFAULT 0,
                out_tx_count INT DEFAULT 0,
                tx_count INT,
                entity_label VARCHAR(128) NULL,
                is_active TINYINT(1) DEFAULT 1,
                last_active_at TIMESTAMP NULL,
                last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_active (is_active)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tx_hash VARCHAR(66) UNIQUE,
                from_addr VARCHAR(42),
                to_addr VARCHAR(42),
                eth_value DECIMAL(36, 18),
                direction VARCHAR(32),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sync_state (
                sync_name VARCHAR(64) PRIMARY KEY,
                last_success_at TIMESTAMP NULL,
                last_row_count INT DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """,
        ]

        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)
                self._ensure_whales_columns(cursor)
                self._ensure_alerts_columns(cursor)
            connection.commit()

    @staticmethod
    def _ensure_whales_columns(cursor) -> None:
        alter_statements = [
            "ALTER TABLE whales ADD COLUMN total_eth_in DECIMAL(36, 18) DEFAULT 0 AFTER address",
            "ALTER TABLE whales ADD COLUMN entity_label VARCHAR(128) NULL",
            "ALTER TABLE whales ADD COLUMN net_flow DECIMAL(36, 18) DEFAULT 0 AFTER total_eth_out",
            "ALTER TABLE whales ADD COLUMN in_tx_count INT DEFAULT 0 AFTER net_flow",
            "ALTER TABLE whales ADD COLUMN out_tx_count INT DEFAULT 0 AFTER in_tx_count",
            "ALTER TABLE whales ADD COLUMN last_active_at TIMESTAMP NULL",
        ]
        for statement in alter_statements:
            try:
                cursor.execute(statement)
            except mysql.connector.Error as exc:
                if exc.errno != 1060:
                    raise

    @staticmethod
    def _ensure_alerts_columns(cursor) -> None:
        cursor.execute("ALTER TABLE alerts MODIFY COLUMN direction VARCHAR(32)")

    def get_active_addresses(self) -> List[str]:
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT address FROM whales WHERE is_active = 1")
                rows = cursor.fetchall()
        return [row[0].lower() for row in rows]

    def save_whale_list(self, rows: Sequence[Mapping[str, object]]) -> int:
        normalized_rows = [self._normalize_whale_row(row) for row in rows]
        active_addresses = [row["address"] for row in normalized_rows]

        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                if normalized_rows:
                    cursor.executemany(
                        """
                        INSERT INTO whales (
                            address,
                            total_eth_in,
                            total_eth_out,
                            net_flow,
                            in_tx_count,
                            out_tx_count,
                            tx_count,
                            entity_label,
                            is_active,
                            last_active_at,
                            last_synced
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, %s, CURRENT_TIMESTAMP)
                        ON DUPLICATE KEY UPDATE
                            total_eth_in = VALUES(total_eth_in),
                            total_eth_out = VALUES(total_eth_out),
                            net_flow = VALUES(net_flow),
                            in_tx_count = VALUES(in_tx_count),
                            out_tx_count = VALUES(out_tx_count),
                            tx_count = VALUES(tx_count),
                            entity_label = VALUES(entity_label),
                            is_active = 1,
                            last_active_at = CASE
                                WHEN VALUES(last_active_at) IS NULL THEN last_active_at
                                WHEN last_active_at IS NULL THEN VALUES(last_active_at)
                                ELSE GREATEST(last_active_at, VALUES(last_active_at))
                            END,
                            last_synced = CURRENT_TIMESTAMP
                        """,
                        [
                            (
                                row["address"],
                                row["total_eth_in"],
                                row["total_eth_out"],
                                row["net_flow"],
                                row["in_tx_count"],
                                row["out_tx_count"],
                                row["tx_count"],
                                row["entity_label"],
                                row["last_active_at"],
                            )
                            for row in normalized_rows
                        ],
                    )

                if active_addresses:
                    placeholders = ", ".join(["%s"] * len(active_addresses))
                    cursor.execute(
                        f"UPDATE whales SET is_active = 0 WHERE address NOT IN ({placeholders})",
                        active_addresses,
                    )
                else:
                    cursor.execute("UPDATE whales SET is_active = 0")

            connection.commit()

        return len(normalized_rows)

    def record_sync_success(self, row_count: int) -> None:
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO sync_state (sync_name, last_success_at, last_row_count)
                    VALUES (%s, CURRENT_TIMESTAMP, %s)
                    ON DUPLICATE KEY UPDATE
                        last_success_at = CURRENT_TIMESTAMP,
                        last_row_count = VALUES(last_row_count)
                    """,
                    ("dune_whale_sync", row_count),
                )
            connection.commit()

    def get_last_sync_at(self) -> datetime | None:
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT last_success_at FROM sync_state WHERE sync_name = %s",
                    ("dune_whale_sync",),
                )
                row = cursor.fetchone()

        if not row or row[0] is None:
            return None

        timestamp = row[0]
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)
        return timestamp

    def save_alert(self, alert: AlertRecord) -> bool:
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO alerts (tx_hash, from_addr, to_addr, eth_value, direction)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE tx_hash = tx_hash
                    """,
                    (
                        alert.tx_hash,
                        alert.from_addr,
                        alert.to_addr,
                        alert.eth_value,
                        alert.direction,
                    ),
                )
                inserted = cursor.rowcount == 1
                if inserted:
                    # Update last_active_at for involved whales
                    cursor.execute(
                        "UPDATE whales SET last_active_at = CURRENT_TIMESTAMP WHERE address = %s",
                        (alert.from_addr,),
                    )
                    cursor.execute(
                        "UPDATE whales SET last_active_at = CURRENT_TIMESTAMP WHERE address = %s",
                        (alert.to_addr,),
                    )
            connection.commit()
        return inserted

    def get_stats(self) -> dict:
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                # Active whale count
                cursor.execute("SELECT COUNT(*) FROM whales WHERE is_active = 1")
                active_whales = cursor.fetchone()[0]

                # 24H Netflow (Withdrawal - Deposit)
                cursor.execute(
                    """
                    SELECT
                        SUM(
                            CASE
                                WHEN direction IN ('Withdrawal', 'BuyETH') THEN eth_value
                                ELSE 0
                            END
                        ) -
                        SUM(
                            CASE
                                WHEN direction IN ('Deposit', 'SellETH') THEN eth_value
                                ELSE 0
                            END
                        ) as netflow
                    FROM alerts
                    WHERE created_at >= NOW() - INTERVAL 1 DAY
                    """
                )
                netflow = cursor.fetchone()[0] or 0

                # Last sync time
                cursor.execute(
                    "SELECT last_success_at FROM sync_state WHERE sync_name = %s",
                    ("dune_whale_sync",),
                )
                last_sync = cursor.fetchone()
                last_sync_at = last_sync[0] if last_sync else None

        next_sync_at = None
        seconds_until_next_sync = None
        if last_sync_at is not None:
            if last_sync_at.tzinfo is None:
                last_sync_at = last_sync_at.replace(tzinfo=timezone.utc)
            else:
                last_sync_at = last_sync_at.astimezone(timezone.utc)
            next_sync_at = last_sync_at + timedelta(hours=self.settings.sync_interval_hours)
            seconds_until_next_sync = max(
                0,
                int((next_sync_at - datetime.now(timezone.utc)).total_seconds()),
            )

        return {
            "active_whales": active_whales,
            "netflow_24h": float(netflow),
            "last_sync_at": self._to_iso_or_none(last_sync_at),
            "next_sync_at": self._to_iso_or_none(next_sync_at),
            "seconds_until_next_sync": seconds_until_next_sync,
            "sync_interval_hours": self.settings.sync_interval_hours,
        }

    def get_latest_alerts(self, limit: int = 50) -> List[dict]:
        with self._get_connection() as connection:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    SELECT tx_hash, from_addr, to_addr, eth_value, direction, created_at
                    FROM alerts
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cursor.fetchall()
        for row in rows:
            row["eth_value"] = float(row["eth_value"])
            if row["created_at"]:
                row["created_at"] = row["created_at"].isoformat()
        return rows

    def get_top_whales(self, limit: int = 10, offset: int = 0) -> List[dict]:
        with self._get_connection() as connection:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    SELECT
                        address,
                        total_eth_in,
                        total_eth_out,
                        net_flow,
                        in_tx_count,
                        out_tx_count,
                        tx_count,
                        entity_label,
                        last_active_at,
                        last_synced
                    FROM whales
                    WHERE is_active = 1
                    ORDER BY ABS(net_flow) DESC, total_eth_out DESC
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset),
                )
                rows = cursor.fetchall()
        for row in rows:
            row["total_eth_in"] = float(row["total_eth_in"])
            row["total_eth_out"] = float(row["total_eth_out"])
            row["net_flow"] = float(row["net_flow"])
            row["last_active_time"] = self._to_iso_or_none(row.get("last_active_at"))
            row["last_synced"] = self._to_iso_or_none(row.get("last_synced"))
        return rows

    def get_whales_count(self) -> int:
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM whales WHERE is_active = 1")
                return cursor.fetchone()[0]

    @staticmethod
    def _normalize_whale_row(row: Mapping[str, object]) -> Mapping[str, object]:
        address = str(row.get("address", "")).strip().lower()
        if not address.startswith("0x") or len(address) != 42:
            raise ValueError(f"Invalid address returned from Dune: {address!r}")

        total_eth_out = Decimal(str(row.get("total_eth_out", "0") or "0"))
        total_eth_in = Decimal(str(row.get("total_eth_in", "0") or "0"))
        net_flow = Decimal(str(row.get("net_flow", "0") or "0"))
        in_tx_count = int(row.get("in_tx_count", 0) or 0)
        out_tx_count = int(row.get("out_tx_count", 0) or 0)
        tx_count = int(row.get("tx_count", 0) or 0)
        entity_label = str(row.get("entity_label", "") or "").strip() or None
        last_active_at = Database._normalize_datetime_value(row.get("last_active_time"))

        return {
            "address": address,
            "total_eth_in": total_eth_in,
            "total_eth_out": total_eth_out,
            "net_flow": net_flow,
            "in_tx_count": in_tx_count,
            "out_tx_count": out_tx_count,
            "tx_count": tx_count,
            "entity_label": entity_label,
            "last_active_at": last_active_at,
        }

    @staticmethod
    def _normalize_datetime_value(value: object) -> datetime | None:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value
            return value.astimezone(timezone.utc).replace(tzinfo=None)

        text = str(value).strip()
        if not text:
            return None
        if text.endswith(" UTC"):
            text = text[:-4] + "+00:00"
        elif text.endswith(" GMT"):
            text = text[:-4] + "+00:00"
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            return parsed
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _to_iso_or_none(value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            else:
                value = value.astimezone(timezone.utc)
            return value.isoformat()
        return str(value)
