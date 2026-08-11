# AI 漫剧制作工作台

将 AI 漫剧制作六步流程（写剧本 → 写分镜 → 定人物+场景 → 批量生图 → 配音配乐 → 剪辑合成）产品化的 Web 工作台。当前处于 Phase 0 脚手架阶段。

## 项目结构

```
backend/    # FastAPI + SQLAlchemy + SQLite + Alembic
frontend/   # Vue3 + Vite + Pinia + Vue Router
```

## 快速启动

```bash
# 后端（8000 端口）
pip install --break-system-packages -r backend/requirements.txt
cd backend && alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端（5173 端口，/api 自动反代到后端）
cd frontend && npm install
npm run dev
```

## 测试

```bash
cd backend && python3 -m pytest tests/ -q
cd frontend && npm run typecheck
```

## 文档

- 需求/设计/任务清单：`.monkeycode/specs/ai-comic-drama-studio/`
- 项目文档：`.monkeycode/docs/`
