这份技术文档已经为你完全重构。针对你指定的 **Python 3.10.4** 环境、**MySQL 数据库**以及 **12小时同步周期** 进行了深度适配。

你可以直接将以下内容保存为 `WhaleEye_Dev_Spec.md` 提供给 CLI。

------

# 📜 Whale-Eye V1.0：Web3 巨鲸实时预警系统开发手册

## 1. 项目架构与目标

本项目是一个高性能的 Web3 后端监控系统。通过 **Dune API** 每 12 小时筛选一次“活跃巨鲸”，并将地址池同步至 **MySQL**。核心进程通过 **Alchemy WebSocket** 维持对这些地址的毫秒级监控，发现大额变动即通过 **Telegram Bot** 推送预警。

------

## 2. 运行环境与依赖 (Environment)

- **Python 版本**: `3.10.4`
- **核心库**:
  - `dune-client`: Dune API 交互。
  - `mysql-connector-python`: MySQL 驱动（带连接池）。
  - `web3`: 以太坊数据解析。
  - `websockets`: Alchemy WSS 通讯。
  - `aiogram`: Telegram 异步框架。
  - `python-dotenv`: 环境变量管理。
  - `apscheduler`: 定时任务管理（用于 12 小时同步控制）。

------

## 3. 环境变量配置 (.env)

Code snippet

```
# --- Dune Configuration ---
DUNE_API_KEY=Pyvm31v3YCZeJgAZq1U203hHBqfmzUoG
DUNE_QUERY_ID=6931437

# --- Alchemy Configuration ---
# 请确保 URL 包含最后的 API Key
ALCHEMY_WSS_URL=wss://eth-mainnet.g.alchemy.com/v2/7t4xcsy4FQfFxfzx6YXUu

# --- Telegram Configuration ---
TG_BOT_TOKEN=8713351700:AAG8YlrXGF3cQl8-OpkcmCIZ0xI-l3Lt5Y0
TG_CHAT_ID=8696085600

# --- MySQL Configuration ---
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=123456
DB_NAME=whale_eye

# --- Business Logic ---
ETH_THRESHOLD=500           # 实时预警门槛 (ETH)
SYNC_INTERVAL_HOURS=12      # 名单更新周期 (12小时)
```

------

## 4. 数据库设计 (MySQL 8.0)

SQL

```
CREATE DATABASE IF NOT EXISTS whale_eye CHARACTER SET utf8mb4;
USE whale_eye;

-- 监控地址池
CREATE TABLE IF NOT EXISTS whales (
    address VARCHAR(42) PRIMARY KEY,
    total_eth_out DECIMAL(36, 18),
    tx_count INT,
    is_active TINYINT(1) DEFAULT 1,
    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_active (is_active)
);

-- 预警历史记录
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tx_hash VARCHAR(66) UNIQUE,
    from_addr VARCHAR(42),
    to_addr VARCHAR(42),
    eth_value DECIMAL(36, 18),
    direction ENUM('Withdrawal', 'Deposit', 'Transfer'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

------

## 5. 模块详细规格

### 5.1 `database.py` (持久化层)

- **连接池**: 使用 `mysql.connector.pooling` 创建连接池（Pool Size: 5）。
- **功能**:
  - `get_active_addresses()`: 返回当前 `is_active=1` 的所有地址列表。
  - `save_whale_list(data)`: 批量更新/插入 Dune 返回的地址，并处理不再活跃的地址（标记 `is_active=0`）。

### 5.2 `sync_engine.py` (Dune 名单同步)

- **调度**: 使用 `APScheduler` 的 `Cron` 或 `Interval` 触发，**每 12 小时**执行一次。
- **逻辑**:
  1. 调用 `DuneClient.run_query(DUNE_QUERY_ID)`。
  2. 提取 `address` 列表，存入 MySQL。
  3. **触发重载**: 同步成功后，通过信号或共享变量通知 `monitor.py` 重新加载地址名单。

### 5.3 `monitor.py` (Alchemy 实时监听器)

- **任务**: 异步长连接，订阅 `alchemy_filteredTransfers`。
- **实时逻辑**:
  - 监听 `fromAddress` 或 `toAddress` 在监控名单中的交易。
  - **大额判断**: 仅处理 `value >= ETH_THRESHOLD` 的交易。
  - **方向识别**:
    - 若 `fromAddress` 为已知交易所（如 Binance）且 `toAddress` 为名单地址 -> **Withdrawal**。
    - 若 `fromAddress` 为名单地址且 `toAddress` 为已知交易所 -> **Deposit**。
  - **重连机制**: 实现 `asyncio` 指数退避重连，并在断线期间记录日志。

### 5.4 `notifier.py` (预警推送)

- **格式**: 采用 HTML 或 MarkdownV2 渲染。
- **字段**: 类型图标 (🚨/🏦)、金额、简写地址、Etherscan 链接。

------

## 6. 给 CLI 的执行 Prompt

> "请基于 Python 3.10.4 开发这个 Web3 监控系统。
>
> 1. 先创建 `requirements.txt` 包含上述所有库。
> 2. 实现 `database.py`，使用 MySQL 连接池，密码为 123456。
> 3. 实现 `sync_engine.py`，使用 APScheduler 设置 12 小时运行一次同步。
> 4. 实现 `monitor.py` 维持与 Alchemy 的异步 WSS 连接，并能动态从数据库重载地址名单。
> 5. 集成 Telegram 推送，确保消息包含交易哈希的超链接。
> 6. 请确保所有 ETH 数值使用 Python 的 `Decimal` 类型进行运算以防精度丢失。"

------

### 💡 开发者建议

1. **Dune 积分节约**: 建议在 `sync_engine.py` 中逻辑：如果距上次成功同步不满 12 小时且程序重启，优先从数据库加载，不触发新的 Dune Query。
2. **异步锁**: 在同步引擎更新数据库和监听器读取名单时，注意线程/协程安全。

这份文档已经完全准备好，请将其交给你的 CLI 开启开发！