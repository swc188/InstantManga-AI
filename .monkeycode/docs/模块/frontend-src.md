# frontend/src

前端工作台壳：应用布局、路由、项目状态与 API 客户端。

## 结构

```
src/
├── main.ts              # 入口：挂载 Vue + Pinia + Router
├── App.vue              # 布局：顶栏 + 六步侧边导航 + 内容区
├── env.d.ts             # Vite 与 .vue 类型声明
├── api/
│   └── client.ts        # request<T>() 统一 API 客户端
├── router/
│   └── index.ts         # 路由表（项目列表 + 六步 + 模型配置）
├── stores/
│   └── project.ts       # Pinia 项目 store
├── components/
│   ├── StepNav.vue      # 六步流程侧边导航
│   └── PlaceholderView.vue  # 通用占位页
└── views/
    ├── ProjectListView.vue   # 项目列表 + 新建项目表单
    ├── ScriptView.vue        # 第一步：剧本（占位）
    ├── StoryboardView.vue    # 第二步：分镜（占位）
    ├── CastingView.vue       # 第三步：定妆（占位）
    ├── GalleryView.vue       # 第四步：生图（占位）
    ├── AudioView.vue         # 第五步：音频（占位）
    ├── StudioView.vue        # 第六步：剪辑（占位）
    └── ModelConfigView.vue   # 模型配置（占位）
```

## 关键文件

| 文件 | 目的 |
|------|------|
| `App.vue` | 布局壳：非六步路由全屏，六步路由显示侧边导航 |
| `router/index.ts` | 六步页面统一 `projects/:id/{step}` 形态 |
| `stores/project.ts` | 项目列表/当前项目/创建（后端端点 Phase 2 实现） |
| `api/client.ts` | 自动加 `/api` 前缀、解析 `{code,message,data}`、`code!==0` 抛错 |

## 依赖

**本模块依赖**:
- `/api` 反向代理到 `http://localhost:8000`（`vite.config.ts`）

**依赖本模块的**:
- 前端页面开发均以本项目结构为基座

## 规范

- 页面组件用 `<script setup>` 组合式 API
- 路由组件放 `views/`，通用组件放 `components/`
- 所有后端调用走 `api/client.ts`，禁止裸 fetch
- 项目相关状态进 Pinia store，页面内不直接持有跨步骤数据
- 新增六步模块页面：建 `views/*.vue` → 注册路由 → StepNav 中步骤已就绪
