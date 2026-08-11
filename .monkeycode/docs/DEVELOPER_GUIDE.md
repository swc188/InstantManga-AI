# 开发者指南

## 项目目的

AI 漫剧制作工作台将 AI 漫剧制作的六步流程产品化为浏览器工作台。当前处于 Phase 0 脚手架阶段，为后续功能开发提供前后端基础骨架。

**核心职责**:
- 后端：FastAPI 统一响应/异常处理 + SQLite 数据层 + Alembic 迁移
- 前端：Vue3 六步导航工作台壳 + API 客户端 + 项目状态管理

## 环境搭建

### 前置条件

- Python >= 3.11
- Node.js >= 22
- FFmpeg（Phase 7 视频合成所需，当前阶段未使用）

### 安装

```bash
# 后端
pip install --break-system-packages -r backend/requirements.txt

# 前端
cd frontend && npm install
```

### 数据库初始化

```bash
cd backend
alembic upgrade head
```

首次执行会创建 `backend/media/studio.db` 及全部 9 张表。修改模型后生成新迁移：

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

### 运行

```bash
# 后端（8000 端口）
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端（5173 端口，/api 自动反代到 8000）
cd frontend && npm run dev
```

### 运行测试

```bash
cd backend && python3 -m pytest tests/ -q
cd frontend && npm run typecheck
```

### 环境变量

| 变量 | 必需 | 描述 | 默认值 |
|------|------|------|--------|
| `ACD_DATABASE_URL` | 否 | SQLite 连接串 | `sqlite:///{backend}/media/studio.db` |
| `ACD_MEDIA_ROOT` | 否 | 素材根目录 | `{backend}/media` |
| `ACD_DEBUG` | 否 | 调试模式 | `true` |
| `ACD_API_PREFIX` | 否 | API 前缀 | `/api` |
| `ACD_CORS_ORIGINS` | 否 | 允许的来源列表 | `["http://localhost:5173"]` |
| `ACD_DEFAULT_MODEL_BASE_URL` | 否 | 默认模型服务 Base URL | `https://agnes-ai.cn` |

配置通过 `backend/.env` 文件或环境变量注入，前缀 `ACD_`，模板见 `backend/.env.example`。

## 开发工作流

### 代码质量工具

| 工具 | 命令 | 目的 |
|------|------|------|
| pytest | `cd backend && python3 -m pytest tests/ -q` | 后端测试 |
| vue-tsc | `cd frontend && npm run typecheck` | 前端类型检查 |
| vite build | `cd frontend && npm run build` | 前端构建（含类型检查） |

### 实施任务流程

按 `.monkeycode/specs/ai-comic-drama-studio/tasklist.md` 推进：每完成一个任务 → 写测试并跑通 → 在 tasklist.md 标记 `[x]` → 同步本文档集。

## 常见任务

### 新增后端业务模块（如剧本模块）

1. 在 `backend/app/models/` 定义/复用 ORM 模型（已有 9 表，脚本等模型已就绪）
2. 在 `backend/app/api/routes/` 新增路由文件，挂载到 `app/api/__init__.py`
3. 业务逻辑放 `backend/app/core/` 或独立 service 模块
4. 在 `backend/tests/` 添加 pytest 测试
5. 如改表结构，生成 Alembic 迁移

### 新增前端页面

1. 在 `frontend/src/views/` 创建页面组件（可先复用 `PlaceholderView`）
2. 在 `frontend/src/router/index.ts` 注册路由
3. 项目相关状态放入 `frontend/src/stores/project.ts`

### 新增数据库迁移

1. 修改 `backend/app/models/` 对应模型
2. `cd backend && alembic revision --autogenerate -m "message"`
3. 审查生成的迁移文件
4. `alembic upgrade head` 并运行测试

## 编码规范

### 后端

- ORM 模型使用 SQLAlchemy 2.0 风格（`Mapped` / `mapped_column`）
- 所有 API 返回统一 `ApiResponse` 结构，异常经 `core/errors.py` 转换
- 模型字段命名使用 snake_case，与 design.md 中的 DDL 保持一致
- 素材路径存相对 `media_root` 的路径

### 前端

- 组合式 API（`<script setup>`），组件文件 PascalCase 命名
- 页面路由组件放 `views/`，通用组件放 `components/`
- API 调用统一走 `src/api/client.ts` 的 `request<T>()`
- 项目状态集中到 Pinia store，页面不直接 fetch

### 测试

- 后端：`tests/test_*.py`，用例名 `test_*`；用 `tmp_path` + `monkeypatch` 隔离文件/配置副作用
- 前端：类型检查通过为基线，逻辑测试后续阶段补充

## 规则与注意

- 禁止删除操作、禁止系统管理类命令；软件安装使用全局模式
- 构建/长驻命令须使用后台终端执行
- 前端配置 `.monkeycode-ai.online` 域名的 allowedHosts 与 `/api` 反代已在 `vite.config.ts` 配置
- API Key 加密（Fernet）与 AI Provider 适配层属 Phase 1，当前未实现
