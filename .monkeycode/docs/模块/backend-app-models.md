# backend/app/models

9 张业务表的 SQLAlchemy 2.0 ORM 模型，与 design.md 中 Data Models 的 DDL 对应。

## 结构

```
models/
├── __init__.py      # 聚合导出全部模型
├── project.py       # projects 表
├── script.py        # scripts 表（content + beats/structure JSON）
├── storyboard.py    # storyboards 表（分镜）
├── character.py     # characters + scenes 两表（角色/场景）
├── shot_asset.py    # shot_assets 表（镜头候选图）
├── audio_asset.py   # audio_assets 表（音频素材）
├── export.py        # exports 表（成片记录）
└── model_config.py  # model_configs 表（模型配置）
```

## 关键文件

| 文件 | 目的 |
|------|------|
| `script.py` | 剧本内容 + 节奏分段（`beats`）与三段结构（`structure`），JSON 列 |
| `storyboard.py` | 分镜行：镜头号、画面描述、景别、台词、情绪、时长 |
| `model_config.py` | 三类能力配置，`api_key_enc` 存密文 |

## 依赖

**本模块依赖**:
- `app/database.py` - `Base` 声明基类

**依赖本模块的**:
- Alembic 迁移（`alembic/env.py` 导入 `app.models` 获取 metadata）
- 后续业务模块 - ORM 查询

## 规范

- 使用 SQLAlchemy 2.0 风格：`Mapped[...]` + `mapped_column`
- 时间字段默认 `datetime.utcnow`，`updated_at` 加 `onupdate`
- JSON 结构（beats/structure）用 `JSON` 类型
- 新增表必须：定义模型 → 导入 `models/__init__.py` → `alembic revision --autogenerate`
