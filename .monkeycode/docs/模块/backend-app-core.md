# backend/app/core

后端核心基础设施：统一响应格式、全局异常处理、素材目录管理。

## 结构

```
core/
├── response.py   # ApiResponse 统一响应模型
├── errors.py     # ApiError 与全局异常处理器
└── storage.py    # 素材目录创建工具
```

## 关键文件

| 文件 | 目的 |
|------|------|
| `response.py` | 定义 `{code, message, data}` 响应模型 |
| `errors.py` | `ApiError` 业务异常 + 404/422/500 异常处理器，全部输出统一格式 |
| `storage.py` | `ensure_project_media()` 幂等创建项目素材子目录 |

## 依赖

**本模块依赖**:
- `app/config.py` - `media_root` 配置

**依赖本模块的**:
- `app/main.py` - 注册异常处理器
- 后续业务模块 - 返回 `ApiResponse`、抛 `ApiError`

## 规范

- 新增业务异常直接 `raise ApiError(status_code, code, message)`
- 业务模块返回值用 `ApiResponse(data=...)`，默认 `code=0`
- 文件操作统一经 `ensure_project_media()` 拿到根目录，不在调用方拼路径
