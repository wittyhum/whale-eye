# Whale-Eye V1.0

Whale-Eye 是一个基于 Python 3.10 的 Web3 巨鲸实时预警系统，主要能力包括：

- 每 12 小时从 Dune 同步一次活跃巨鲸地址名单
- 将监控地址池持久化到 MySQL
- 通过 Alchemy WebSocket 实时监听大额链上转账
- 将符合条件的预警消息推送到 Telegram
- 支持第一版 `稳定币 <-> WETH/ETH` 买卖语义识别
- 所有 ETH 金额统一使用 `Decimal` 处理，避免精度丢失

## 项目功能

系统由以下几个核心流程组成：

1. `sync_engine.py` 定时从 Dune 拉取最新巨鲸名单
2. `database.py` 将名单写入 MySQL，并维护活跃地址状态
3. `monitor.py` 通过 Alchemy WebSocket 持续监听相关地址交易
4. 当交易金额达到阈值时，`notifier.py` 会向 Telegram 发送告警
5. 系统会对部分交易进行语义识别，输出 `BuyETH` / `SellETH` / `Deposit` / `Withdrawal`
6. `main.py` 负责组装并启动整个服务

## 运行环境

- Python：`3.10.4`
- MySQL：建议 `8.0+`
- 操作系统：Windows / macOS / Linux 均可

## 安装步骤

### 1. 创建虚拟环境

```bash
python -m venv .venv
```

Windows 激活：

```bash
.venv\Scripts\activate
```

macOS / Linux 激活：

```bash
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

将 [.env.example](D:\web3infor\.env.example) 复制为 `.env`，然后填写你自己的配置项。

示例配置说明：

- `DUNE_API_KEY`：Dune API Key
- `DUNE_QUERY_ID`：Dune 查询 ID
- `ALCHEMY_WSS_URL`：Alchemy WebSocket 地址
- `ALCHEMY_HTTP_URL`：Alchemy HTTP RPC 地址，可留空并由程序根据 WSS 地址自动推导
- `TG_BOT_TOKEN`：Telegram 机器人 Token
- `TG_CHAT_ID`：接收告警的聊天 ID
- `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME`：MySQL 连接信息
- `ETH_THRESHOLD`：触发预警的最小 ETH 数量
- `SYNC_INTERVAL_HOURS`：同步巨鲸名单的周期，默认 12 小时
- `KNOWN_EXCHANGES_JSON`：已知交易所地址映射，用于判断充值或提现方向

## 启动方式

项目启动入口是 [main.py](D:\web3infor\main.py)。

在项目根目录执行：

```bash
python main.py
```

如果你使用 PyCharm：

- 运行文件选择 [main.py](D:\web3infor\main.py)
- Working directory 设置为 `D:\web3infor`
- Python Interpreter 选择 `Python 3.10.4`

## 目录说明

- [config.py](D:\web3infor\config.py)：读取 `.env` 并生成运行配置
- [database.py](D:\web3infor\database.py)：MySQL 连接池、建库建表、地址池保存、告警记录去重
- [sync_engine.py](D:\web3infor\sync_engine.py)：Dune 数据同步与 12 小时定时任务
- [monitor.py](D:\web3infor\monitor.py)：Alchemy 实时监听、金额阈值过滤、方向识别、断线重连
- [notifier.py](D:\web3infor\notifier.py)：Telegram 告警消息推送
- [main.py](D:\web3infor\main.py)：项目主入口，负责组装和启动所有模块
- [requirements.txt](D:\web3infor\requirements.txt)：项目依赖列表

## 数据库说明

程序启动时会自动尝试创建数据库和所需表结构，核心表包括：

- `whales`：当前监控的巨鲸地址池
- `alerts`：历史预警记录，用于避免重复发送
- `sync_state`：同步状态记录，用于避免程序重启后短时间内重复请求 Dune

## 业务规则说明

- 仅当交易金额大于等于 `ETH_THRESHOLD` 时才会触发预警
- 如果转出地址是交易所、转入地址是巨鲸地址，则识别为 `Withdrawal`
- 如果转出地址是巨鲸地址、转入地址是交易所，则识别为 `Deposit`
- 如果巨鲸使用稳定币换入 `WETH/ETH`，则识别为 `BuyETH`
- 如果巨鲸卖出 `WETH/ETH` 换成稳定币，则识别为 `SellETH`
- 其他情况识别为 `Transfer`

## 注意事项

- 请不要把真实的 API Key 和机器人 Token 提交到代码仓库
- 首次运行前请确保 MySQL 服务已经启动，并且账号密码正确
- 如果 Alchemy 的订阅方式和当前默认值不一致，可以在 `.env` 中调整：
  - `ALCHEMY_SUBSCRIPTION_METHOD`
  - `ALCHEMY_SUBSCRIPTION_TYPE`
- `KNOWN_EXCHANGES_JSON` 为空时，系统仍可运行，但方向识别会更多落到 `Transfer`

## 示例运行流程

1. 程序启动
2. 初始化 MySQL 数据库与表结构
3. 检查最近一次 Dune 同步时间
4. 如果超过 12 小时，则重新同步巨鲸地址名单
5. 建立 Alchemy WebSocket 长连接
6. 实时监听大额转账
7. 发现命中条件的交易后写入 `alerts` 并推送 Telegram 消息

## 后续可扩展方向

- 增加更多链支持，例如 Base、Arbitrum、BSC
- 增加 Web 管理后台查看巨鲸名单和告警历史
- 增加 Redis 缓存和任务队列提升吞吐能力
- 增加 Prometheus / Grafana 监控
- 增加 Docker 与 Docker Compose 一键部署
