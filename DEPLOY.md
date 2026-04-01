# Whale-Eye 云服务器 Docker 部署说明

本文档采用安全方式部署，并默认使用服务器上已经安装好的 MySQL：

- 真实密钥只保存在服务器的 `.env`
- 镜像中不写入真实 API Key、Bot Token 或数据库密码
- 仓库中只保留 `.env.example` 作为模板
- Docker 只运行应用容器，不再额外启动 MySQL 容器

## 一、准备条件

部署前请确认服务器具备以下条件：

- Linux 云服务器一台
- 已安装 Docker
- 已安装 Docker Compose Plugin
- 服务器可以访问：
  - Dune API
  - Alchemy WebSocket
  - Telegram API

建议系统版本：

- Ubuntu 22.04 LTS
- Debian 12

## 二、上传项目到云服务器

将整个项目目录上传到服务器，例如：

```bash
/opt/whale-eye
```

你可以使用以下任一方式：

1. `git clone`
2. SFTP / Xftp / FinalShell 上传
3. 本地压缩后上传再解压

上传后目录示例：

```bash
/opt/whale-eye
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── main.py
├── config.py
├── database.py
├── sync_engine.py
├── monitor.py
├── notifier.py
└── README.md
```

## 三、在服务器创建 .env

进入项目目录：

```bash
cd /opt/whale-eye
```

复制模板：

```bash
cp .env.example .env
```

编辑 `.env`：

```bash
nano .env
```

填写你自己的真实配置，例如：

```env
DUNE_API_KEY=你的真实DuneKey
DUNE_QUERY_ID=6931437

ALCHEMY_WSS_URL=wss://eth-mainnet.g.alchemy.com/v2/你的真实AlchemyKey
ALCHEMY_SUBSCRIPTION_METHOD=alchemy_subscribe
ALCHEMY_SUBSCRIPTION_TYPE=alchemy_filteredTransfers

TG_BOT_TOKEN=你的真实TelegramBotToken
TG_CHAT_ID=你的真实TelegramChatId

DB_HOST=host.docker.internal
DB_PORT=3306
DB_USER=你的MySQL用户名
DB_PASSWORD=你的MySQL密码
DB_NAME=whale_eye
DB_POOL_SIZE=5

ETH_THRESHOLD=500
SYNC_INTERVAL_HOURS=12
ADDRESS_REFRESH_SECONDS=300
RECONNECT_MAX_SECONDS=60
LOG_LEVEL=INFO

KNOWN_EXCHANGES_JSON={}
```

说明：

- 如果数据库部署在当前服务器宿主机上，`DB_HOST` 建议写成 `host.docker.internal`
- 当前 `docker-compose.yml` 已通过 `extra_hosts` 将 `host.docker.internal` 映射到宿主机
- 如果使用云数据库，请把 `DB_HOST` 改成对应数据库地址

## 四、构建并启动容器

在项目目录执行：

```bash
docker compose up -d --build
```

这条命令会：

1. 构建 Whale-Eye 应用镜像
2. 启动应用容器
3. 自动将 `.env` 注入应用容器

## 五、查看运行状态

查看容器：

```bash
docker compose ps
```

查看应用日志：

```bash
docker compose logs -f app
```

如果启动正常，你会看到类似日志：

- 数据库初始化完成
- Dune 名单同步成功
- Alchemy websocket connected

## 六、验证数据库是否创建成功

登录宿主机上的 MySQL 后执行：

```sql
SHOW DATABASES;
USE whale_eye;
SHOW TABLES;
```

正常情况下会看到以下表：

- `whales`
- `alerts`
- `sync_state`

## 七、常用运维命令

停止服务：

```bash
docker compose down
```

重新构建并启动：

```bash
docker compose up -d --build
```

重启应用容器：

```bash
docker compose restart app
```

## 八、安全建议

请务必遵守以下规则：

1. 不要把真实 `.env` 上传到 Git 仓库
2. 不要把真实密钥写进 `Dockerfile`
3. 不要把真实密钥写进 `docker-compose.yml`
4. 不要把带密钥的镜像推送到公开仓库
5. 如果密钥曾在聊天、截图、仓库或日志中暴露，请立刻重置

## 九、故障排查

### 1. 应用容器反复重启

执行：

```bash
docker compose logs -f app
```

常见原因：

- `.env` 没创建
- `.env` 里的值为空
- Dune Key / Alchemy Key / Telegram Token 配置错误
- 数据库连不上

### 2. MySQL 连接失败

检查：

- `DB_HOST` 是否为 `host.docker.internal` 或正确的云数据库地址
- `DB_USER`、`DB_PASSWORD`、`DB_NAME` 是否正确
- 宿主机 MySQL 是否已正常启动

### 3. 收不到 Telegram 消息

检查：

- `TG_BOT_TOKEN` 是否正确
- `TG_CHAT_ID` 是否正确
- 机器人是否已经向对应用户或群发送过消息并具有权限

### 4. 没有监控到转账

检查：

- Dune 查询是否真的返回地址
- `ETH_THRESHOLD` 是否过高
- Alchemy WebSocket Key 是否有效
- 地址名单是否已经写入 `whales` 表
