# AI 漫剧制作工作台 文档

本文档集描述 AI 漫剧制作工作台的系统架构、接口契约与开发指南。当前项目处于 Phase 0 脚手架阶段，六步业务模块为框架占位，文档反映真实代码现状。

**快速链接**: [架构](./ARCHITECTURE.md) | [接口](./INTERFACES.md) | [开发者指南](./DEVELOPER_GUIDE.md)

---

## 核心文档

### [架构](./ARCHITECTURE.md)
系统设计、技术栈、组件结构和数据流。了解系统如何运作的起点。

### [接口](./INTERFACES.md)
统一响应格式、HTTP 端点、前端路由与数据库 Schema。集成或开发 API 的参考。

### [开发者指南](./DEVELOPER_GUIDE.md)
环境搭建、运行测试、常见任务与编码规范。贡献者必读。

---

## 模块

| 模块 | 描述 | README |
|------|------|--------|
| `backend/app/core/` | 统一响应、异常处理、素材目录管理 | [README](./模块/backend-app-core.md) |
| `backend/app/models/` | 9 张业务表的 ORM 模型 | [README](./模块/backend-app-models.md) |
| `frontend/src/` | Vue3 工作台壳、路由、状态、API 客户端 | [README](./模块/frontend-src.md) |

---

## 核心概念

| 概念 | 描述 |
|------|------|
| [统一响应格式](./专有概念/统一响应格式.md) | 后端所有响应的 `{code, message, data}` 契约 |
| [项目](./专有概念/项目.md) | 一次漫剧制作任务的完整载体 |
| [模型配置](./专有概念/模型配置.md) | 用户自配三类 AI 能力的配置条目 |
| [素材目录](./专有概念/素材目录.md) | 按项目组织的本地素材文件结构 |

---

## 入门指南

### 项目新人？

1. **[架构](./ARCHITECTURE.md)** - 了解全局
2. **[项目](./专有概念/项目.md)** - 学习核心数据模型
3. **[开发者指南](./DEVELOPER_GUIDE.md)** - 搭建环境

### 首次贡献？

1. **[开发者指南](./DEVELOPER_GUIDE.md)** - 搭建与工作流
2. **[模块 README](./模块/frontend-src.md)** - 了解前端结构
3. 按 **[tasklist](../specs/ai-comic-drama-studio/tasklist.md)** 认领任务

---

## 快速参考

### 命令

```bash
cd backend && python3 -m pytest tests/ -q   # 后端测试
cd backend && alembic upgrade head           # 数据库迁移
cd frontend && npm run dev                   # 前端开发服务器
cd frontend && npm run build                 # 前端构建
```

### 重要文件

| 文件 | 目的 |
|------|------|
| `backend/app/main.py` | 后端应用入口 |
| `backend/alembic/` | 数据库迁移脚本 |
| `frontend/src/router/index.ts` | 前端路由定义 |
| `frontend/vite.config.ts` | 反代与 allowedHosts 配置 |
