这份文档是为你专门设计的 **Whale-Eye Dashboard 前端开发指南**。它采用了 2026 年最主流的 Web3 审美标准，并针对你的后端（FastAPI + MySQL）进行了数据对接优化。

你可以直接将以下内容存为 `Frontend_Spec.md` 并发给 CLI。

------

# 🎨 Whale-Eye Dashboard：前端开发技术手册 (V1.0)

## 1. 项目定位

Whale-Eye 前端是一个**高频数据看板**，旨在以极具“科技感”的视觉方式展示以太坊巨鲸的实时动态。它不仅是数据的展示窗口，更是 Web3 资产流向的风向标。

------

## 2. 技术栈 (Technical Stack)

- **框架**: `Next.js 14/15` (App Router) - 提供极佳的加载速度和 SEO。
- **样式**: `Tailwind CSS` - 用于快速构建响应式、高性能 UI。
- **组件库**: `Shadcn UI` + `Lucide React` (图标) - 保持专业一致的 UI 规范。
- **动效**: `Framer Motion` - 实现数据卡片的“流式”滑入和点击反馈。
- **可视化**: `Apache ECharts` - 处理巨鲸关联图和资金流向图。
- **状态管理/取数**: `SWR` 或 `React Query` - 实现对 FastAPI 接口的自动轮询与缓存。

------

## 3. 视觉规范 (Visual Identity)

- **主题**: 强制 Dark Mode (深色模式)。
  - 背景色: `#0B0E11` (深空黑)
  - 卡片背景: `rgba(23, 27, 34, 0.8)` (半透明磨砂)
  - 主色 (强调): `#00FFA3` (极光绿 - 代表流入/看涨)
  - 辅助色 (警告): `#FF3B69` (霓虹红 - 代表流出/看跌)
- **风格**: **Glassmorphism (玻璃拟态)**。所有容器需具备 `backdrop-filter: blur(10px)` 和细腻的 1px 边框。

------

## 4. 页面布局设计 (Layout)

整个页面分为三个功能核心区：

### 4.1 顶部数据概览 (Stats Ribbon)

- **指标 1**: `24H Netflow` (实时滚动的 ETH 净流向数字)。
- **指标 2**: `Active Whales` (当前数据库中活跃的巨鲸总数)。
- **指标 3**: `System Status` (显示 API 连通性与上次同步时间)。

### 4.2 核心：实时异动流 (Live Transaction Feed)

- **功能**: 实时显示从 `/api/alerts` 接口获取的最新转账。
- **交互**: 每当有新数据时，新卡片从顶部“平滑推入”。
- **内容**:
  - 巨鲸头像 (根据地址生成的 Identicon)。
  - 醒目的金额（例如：`2,450 ETH`）。
  - 带有动画箭头的流向（例如：`Binance 14 ➔ 0x71c...`）。
  - 一键跳转 Etherscan 的图标。

### 4.3 侧边栏/底栏：巨鲸画像 (Whale List)

- **功能**: 展示 `whales` 表中的 TOP 10 地址。
- **可视化**: 一个简单的柱状图，展示各巨鲸在过去 12 小时的转账频次。

------

## 5. API 对接规范 (Backend Integration)

前端需从后端（FastAPI）获取以下三个核心接口：

1. `GET /api/stats`: 返回汇总数据（总额、活跃数）。
2. `GET /api/whales`: 返回监控名单（用于列表展示）。
3. `GET /api/alerts`: 返回历史报警记录（按时间倒序）。

------

## 6. 环境配置 (`frontend/.env.local`)

Code snippet

```
# 指向后端容器或服务器地址
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

------

## 7. 给 CLI 的执行 Prompt (重点)

> "请基于 Next.js 14 和 Tailwind CSS 开发 Whale-Eye 前端。
>
> 1. **目录结构**: 严格遵循 App Router 模式。
> 2. **视觉风格**: 实现深色模式和玻璃拟态（Glassmorphism）。
> 3. **核心组件**:
>    - `WhaleStats`: 顶部横向滚动的数据卡片。
>    - `AlertFeed`: 实时异动流，使用 `framer-motion` 实现新数据入场动画。
>    - `WhaleCard`: 展示单个地址详情的精美卡片。
> 4. **数据逻辑**: 使用 `SWR` 每 5 秒轮询一次 `/api/alerts` 接口，并确保 UI 不闪烁。
> 5. **响应式**: 适配手机端，在小屏幕上自动隐藏复杂的图表。
> 6. **Docker**: 提供一个 `Dockerfile`，使用 `node:18-alpine` 进行多阶段构建（Build & Serve）。"

------

## 8. 部署建议

- **方式**: 前端代码放在项目的 `frontend/` 文件夹下。
- **容器化**: 在 `docker-compose.yml` 中配置前端容器，映射端口 `3000:3000`。
- **开源建议**: 在 `README.md` 中展示一张高保真的 Dashboard 截图，这能直接提升项目的吸引力。

### 🚀 总结

这份文档已经把“高级感”的实现路径说得很清楚了。你现在只需要把后端（FastAPI）的接口先写好，然后把这份文档丢给 CLI，它就能帮你画出一个极其酷炫的 Web3 看板。