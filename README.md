# Whale-Eye

Whale-Eye 是一个面向 Ethereum 主网的 Web3 巨鲸监控与预警系统，用于同步活跃巨鲸地址、实时监听链上大额资金流动、识别部分交易语义，并将告警结果推送到 Telegram，同时提供一个可视化前端面板用于查看监控名单、统计信息和最新告警。

项目当前由两部分组成：

- 后端服务：负责巨鲸名单同步、链上监听、语义识别、告警推送和数据接口输出
- 前端看板：负责展示系统状态、巨鲸列表、巨鲸画像和语义化告警时间轴

## 项目特性

- 基于 Dune 查询结果定时同步巨鲸地址池
- 使用 Alchemy WebSocket 实时监听巨鲸地址相关转账事件
- 使用 MySQL 持久化监控地址、同步状态与历史告警
- 支持 Telegram 机器人告警推送
- 支持 `Withdrawal`、`Deposit`、`Transfer`、`BuyETH`、`SellETH` 等语义识别
- 对 ETH 数值统一使用 `Decimal` 处理，减少精度误差
- 提供 FastAPI 接口供前端看板消费
- 提供 Next.js 前端仪表盘查看监控状态与最新告警
- 支持 Docker / Docker Compose 部署

## 适用场景

- 监控重点地址的大额转账行为
- 跟踪巨鲸与中心化交易所之间的资金流向
- 辅助判断 ETH 买入、卖出、充值、提现等市场信号
- 构建自有 Web3 风控、情报或告警系统的基础模块

## 系统架构

```text
Dune Query
   -> WhaleSyncEngine
   -> MySQL.whales / sync_state
   -> WhaleMonitor
   -> Alchemy WebSocket + HTTP RPC
   -> Semantic Classification
   -> MySQL.alerts
   -> Telegram Notifier
   -> FastAPI
   -> Next.js Dashboard
```

## 技术栈

### 后端

| 类别 | 技术 |
| --- | --- |
| 语言 | Python 3.10 |
| Web 框架 | FastAPI |
| 服务启动 | Uvicorn |
| 定时任务 | APScheduler |
| 链上访问 | Web3.py |
| WebSocket | websockets |
| 数据库 | MySQL |
| 数据校验 / 配置 | dataclasses、python-dotenv、Pydantic 相关依赖 |
| 消息通知 | aiogram |
| 容器化 | Docker |

### 前端

| 类别 | 技术 |
| --- | --- |
| 框架 | Next.js 14 |
| UI 基础 | React 18 |
| 语言 | TypeScript |
| 样式 | Tailwind CSS |
| 动效 | Framer Motion |
| 数据请求 | SWR |
| 图标 | lucide-react |

## 第三方库

### Python 依赖

| 库名 | 用途 |
| --- | --- |
| `dune-client` | 调用 Dune 查询结果，同步巨鲸地址数据 |
| `mysql-connector-python` | 连接 MySQL，并提供连接池能力 |
| `web3` | 获取交易回执、解析链上事件与转账语义 |
| `websockets` | 建立与 Alchemy 的 WebSocket 长连接 |
| `aiogram` | 发送 Telegram 机器人消息 |
| `python-dotenv` | 加载 `.env` 配置 |
| `APScheduler` | 定时触发巨鲸名单同步任务 |
| `aiohttp-socks` | Telegram 代理支持 |
| `fastapi` | 提供后端 HTTP API |
| `uvicorn` | 运行 ASGI 服务 |
| `pydantic` / `pydantic-settings` | 配置与数据建模相关依赖 |

### 前端依赖

| 库名 | 用途 |
| --- | --- |
| `next` | 前端应用框架 |
| `react` / `react-dom` | 组件渲染 |
| `swr` | 轮询与缓存后端 API 数据 |
| `framer-motion` | 告警时间轴与界面动画 |
| `lucide-react` | 图标组件 |
| `clsx` | 条件类名拼接 |
| `tailwind-merge` | Tailwind 类名合并 |
| `tailwindcss` / `postcss` / `autoprefixer` | 样式构建链路 |

## 外部 API 与服务

项目运行依赖以下外部服务：

| 服务 | 用途 |
| --- | --- |
| Dune API | 获取巨鲸地址查询结果 |
| Alchemy WebSocket API | 实时订阅地址相关转账事件 |
| Alchemy HTTP RPC | 获取交易回执并做语义识别 |
| Telegram Bot API | 发送预警消息 |
| MySQL | 存储地址池、同步状态、历史告警 |

项目还会使用以下外部站点能力：

- Etherscan：在告警消息和前端中跳转查看链上交易详情
- DiceBear：前端根据地址生成 identicon 头像

## 功能说明

### 1. 巨鲸名单同步

- 定时从 Dune 拉取最新巨鲸地址列表
- 支持按配置的同步周期自动执行
- 将地址写入数据库，并维护活跃 / 非活跃状态
- 记录最近一次成功同步时间与同步条数

### 2. 实时链上监听

- 通过 Alchemy WebSocket 监听监控地址的转入与转出事件
- 同时监听外部转账与 ERC-20 转账
- 支持连接断开后的自动重连
- 支持地址池变更后自动重新订阅
- 记录 WebSocket ping 延迟，用于展示链路健康状态

### 3. 交易语义识别

- 识别巨鲸从交易所提现为 `Withdrawal`
- 识别巨鲸向交易所充值为 `Deposit`
- 识别普通大额转账为 `Transfer`
- 识别稳定币换入 `WETH / ETH` 为 `BuyETH`
- 识别 `WETH / ETH` 卖出换成稳定币为 `SellETH`
- 对未能确认语义的交易执行阈值过滤后再决定是否告警

### 4. 告警与通知

- 对命中阈值的交易写入历史告警表
- 基于交易哈希去重，避免重复推送
- 通过 Telegram 机器人向指定聊天发送格式化告警
- 告警内容包含方向、金额、地址标签和 Etherscan 链接

### 5. 前端可视化看板

- 展示当前活跃巨鲸数量
- 展示下次同步倒计时
- 展示 WebSocket ping 状态
- 展示巨鲸分页列表与基础画像
- 展示单个地址的流入、流出、净流、交易次数和最近活跃时间
- 展示最新语义化告警时间轴

## 后端 API

当前后端提供以下接口：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/stats` | 返回系统统计信息、同步状态、WSS ping |
| `GET` | `/api/whales` | 返回巨鲸列表，支持分页参数 |
| `GET` | `/api/alerts` | 返回最新告警列表 |
| `GET` | `/health` | 健康检查接口 |

### `/api/stats`

主要返回内容包括：

- `active_whales`
- `netflow_24h`
- `last_sync_at`
- `next_sync_at`
- `seconds_until_next_sync`
- `sync_interval_hours`
- `wss_ping_ms`

### `/api/whales`

主要返回内容包括：

- 地址
- 流入 ETH 总量
- 流出 ETH 总量
- 净流量
- 交易次数
- 实体标签
- 最近活跃时间
- 最近同步时间

### `/api/alerts`

主要返回内容包括：

- 交易哈希
- 转出地址
- 转入地址
- ETH 金额
- 方向标签
- 创建时间

## 目录结构

```text
.
├─ main.py                # FastAPI 入口，初始化同步、监听与接口
├─ config.py              # 环境变量读取与配置对象
├─ database.py            # MySQL 初始化、数据读写、统计查询
├─ sync_engine.py         # Dune 数据同步与定时调度
├─ monitor.py             # Alchemy 监听、语义识别、阈值过滤、重连
├─ notifier.py            # Telegram 消息推送
├─ migrate_db.py          # 数据库迁移辅助脚本
├─ requirements.txt       # Python 依赖
├─ Dockerfile             # 后端镜像构建
├─ docker-compose.yml     # 前后端联合部署
└─ frontend/              # Next.js 前端面板
   ├─ app/
   ├─ components/
   ├─ lib/
   ├─ package.json
   └─ Dockerfile
```

## 数据库设计

系统启动时会自动创建数据库和表结构，核心表如下：

| 表名 | 说明 |
| --- | --- |
| `whales` | 当前监控的巨鲸地址池与画像数据 |
| `alerts` | 历史告警记录，用于展示与去重 |
| `sync_state` | Dune 同步状态与最近成功时间 |

## 环境变量

项目通过 `.env` 管理运行配置，关键字段如下：

| 变量名 | 说明 |
| --- | --- |
| `DUNE_API_KEY` | Dune API Key |
| `DUNE_QUERY_ID` | Dune 查询 ID |
| `ALCHEMY_WSS_URL` | Alchemy WebSocket 地址 |
| `ALCHEMY_HTTP_URL` | Alchemy HTTP RPC 地址，可为空 |
| `ALCHEMY_SUBSCRIPTION_METHOD` | WebSocket 订阅方法名 |
| `ALCHEMY_SUBSCRIPTION_TYPE` | 订阅类型 |
| `TG_BOT_TOKEN` | Telegram Bot Token |
| `TG_CHAT_ID` | Telegram 聊天 ID |
| `TG_PROXY` | Telegram 代理地址，可选 |
| `DB_HOST` | MySQL 主机 |
| `DB_PORT` | MySQL 端口 |
| `DB_USER` | MySQL 用户名 |
| `DB_PASSWORD` | MySQL 密码 |
| `DB_NAME` | 数据库名称 |
| `DB_POOL_SIZE` | MySQL 连接池大小 |
| `ETH_THRESHOLD` | 告警触发的最小 ETH 阈值 |
| `SYNC_INTERVAL_HOURS` | Dune 同步周期 |
| `ADDRESS_REFRESH_SECONDS` | 地址池刷新周期 |
| `RECONNECT_MAX_SECONDS` | WebSocket 最大重连间隔 |
| `LOG_LEVEL` | 日志级别 |
| `KNOWN_EXCHANGES_JSON` | 已知交易所地址映射 |
| `NEXT_PUBLIC_API_BASE_URL` | 前端请求后端 API 的基础地址 |

## 快速开始

### 1. 准备环境

- Python 3.10+
- Node.js 18+
- MySQL 8.0+

### 2. 安装后端依赖

在项目根目录安装：

```bash
pip install -r requirements.txt
```

### 3. 安装前端依赖

在 `frontend` 目录安装：

```bash
npm install
```

### 4. 配置环境变量

- 将 `.env.example` 复制为 `.env`
- 填入 Dune、Alchemy、Telegram、MySQL 等配置
- 如果部署前端，需要正确配置 `NEXT_PUBLIC_API_BASE_URL`

### 5. 启动后端

```bash
python main.py
```

默认监听端口为 `8000`。

### 6. 启动前端

```bash
cd frontend
npm run dev
```

默认访问地址为 `http://localhost:3000`。

## Docker 部署

项目已提供前后端镜像与 `docker-compose.yml`，适合快速部署：

```bash
docker compose up --build -d
```

默认暴露端口：

- `8000`：后端 API
- `3000`：前端看板

## 运行流程

1. 服务启动并加载环境变量
2. 初始化 MySQL 数据库与表结构
3. 读取本地地址池并启动定时同步任务
4. 根据同步结果刷新监控地址集合
5. 通过 Alchemy 建立实时监听连接
6. 对交易进行金额过滤与语义识别
7. 将告警写入数据库并推送到 Telegram
8. 由 FastAPI 提供数据接口，前端定时轮询展示

## 当前实现范围

- 当前默认围绕 Ethereum 主网工作
- 当前语义识别重点覆盖 ETH / WETH 与主流稳定币之间的行为
- 当前通知渠道为 Telegram
- 当前前端为监控看板，不包含复杂后台管理能力

## 注意事项

- 不要将真实的 API Key、Bot Token 或数据库密码提交到仓库
- 首次运行前请确认 MySQL 服务可用
- 若 Dune 查询返回字段名变化，需同步调整数据清洗逻辑
- `KNOWN_EXCHANGES_JSON` 为空时，部分方向识别会回退为 `Transfer`
- 前端依赖后端 API 可访问性，部署时请确认跨域与地址配置正确

## 可扩展方向

- 增加更多链支持，例如 Base、Arbitrum、BSC
- 增加更多协议语义识别，而不仅限于稳定币与 WETH
- 增加 Redis、消息队列与更高吞吐的异步处理链路
- 增加权限体系、后台管理与告警订阅管理
- 增加指标监控、审计日志和可观测性组件
- 增加更多通知渠道，例如企业微信、Discord、Slack

## License

如需开源发布，建议补充明确的 License 文件。
