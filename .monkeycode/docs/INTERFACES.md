# 接口文档

## 统一响应格式

后端所有响应使用统一 JSON 结构：

```json
{
  "code": 0,
  "message": "ok",
  "data": null
}
```

- `code`: 0 表示成功，非 0 表示错误码（默认等于 HTTP 状态码）
- `message`: 人类可读消息
- `data`: 业务数据

**错误响应示例（404）**：
```json
{
  "code": 404,
  "message": "Not Found",
  "data": null
}
```

## HTTP 端点

### 健康检查

`GET /api/health`

| 项 | 值 |
|----|----|
| 成功响应 | `data.status = "ok"` |

**响应示例**：
```json
{
  "code": 0,
  "message": "ok",
  "data": { "status": "ok" }
}
```

### 模型配置

`GET /api/model-config`

返回三类能力（text/image/tts）的已保存配置列表，API Key 以掩码展示（如 `sk-a****1234`）。

`PUT /api/model-config/{capability}`

保存/更新某一能力的配置。请求体：`provider_type`（openai_compatible/jimeng/keling）、`base_url`、`api_key`（留空表示保留原 Key）、`model_name`。保存后 `is_valid` 重置为 0。

`POST /api/model-config/test`

对传入的临时配置做连通性测试。请求体含 `capability`、`provider_type`、`base_url`、`api_key`、`model_name`。返回 `{ok: bool}`，失败时 `code=1` 且 message 为可读原因。

`POST /api/model-config/{capability}/test`

对已保存配置做连通性测试，通过后将 `is_valid` 置为 1。

### OpenAPI

- Swagger UI: `GET /api/docs`
- OpenAPI JSON: `GET /api/openapi.json`

## 计划中的端点（后续阶段实现）

以下端点已在设计文档（`../specs/ai-comic-drama-studio/design.md`）中规划，Phase 1-7 逐步落地：

| 模块 | 端点 | 阶段 |
|------|------|------|
| 项目 | `POST /projects`、`GET /projects`、`GET/PUT /projects/{id}` | Phase 2 |
| 剧本 | `POST /projects/{id}/script/generate`、`PUT /projects/{id}/script` | Phase 2 |
| 分镜 | `POST /projects/{id}/storyboard/generate`、`GET/PUT /projects/{id}/storyboard` | Phase 3 |
| 角色/场景 | `POST /projects/{id}/characters`、`POST /projects/{id}/scenes` | Phase 4 |
| 生图 | `POST /projects/{id}/images/generate` | Phase 5 |
| 音频 | `POST /projects/{id}/audio/voice|bgm|sfx` | Phase 6 |
| 合成 | `POST /projects/{id}/compose/preview|export` | Phase 7 |

## 前端 API 客户端

`frontend/src/api/client.ts` 封装 `request<T>()`：自动加 `/api` 前缀、解析统一响应、非 0 `code` 抛 `ApiError`。

```typescript
import { request } from '../api/client'

const data = await request<Project[]>('/projects')
```

## 前端路由

| 路径 | 名称 | 页面 |
|------|------|------|
| `/` | - | 重定向到 `/projects` |
| `/projects` | projects | 项目列表 |
| `/projects/:id/script` | script | 第一步：剧本 |
| `/projects/:id/storyboard` | storyboard | 第二步：分镜 |
| `/projects/:id/casting` | casting | 第三步：定妆 |
| `/projects/:id/gallery` | gallery | 第四步：生图 |
| `/projects/:id/audio` | audio | 第五步：音频 |
| `/projects/:id/studio` | studio | 第六步：剪辑 |
| `/settings/models` | model-config | 模型配置 |

## 数据库 Schema

SQLite 库 `backend/media/studio.db`，由 Alembic 迁移管理（初始迁移 `1572b430419e`）。

### 表清单

| 表 | 用途 | 关键字段 |
|----|------|---------|
| `projects` | 项目 | title, genre, status |
| `scripts` | 剧本 | project_id, content, beats(JSON), structure(JSON) |
| `storyboards` | 分镜 | project_id, shot_no, scene_desc, shot_type, camera_angle, dialogue, emotion, duration, image_id |
| `characters` | 角色 | project_id, name, keywords, portrait_path |
| `scenes` | 场景 | project_id, name, desc_words |
| `shot_assets` | 镜头候选图 | storyboard_id, file_path, is_selected, style_score |
| `audio_assets` | 音频素材 | project_id, kind, storyboard_id, file_path, emotion, volume, align_shot |
| `exports` | 成片记录 | project_id, file_path, resolution, duration |
| `model_configs` | 模型配置 | capability(unique), provider_type, base_url, api_key_enc, model_name, is_valid |

外键关系：scripts/storyboards/characters/scenes/audio_assets/exports 均属于 `projects`；shot_assets 属于 `storyboards`。
