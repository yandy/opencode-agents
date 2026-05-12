# oca-tool uninstall Design Spec

## Overview

`oca-tool uninstall` 命令用于安全地清理 `oca-tool install` 在当前项目中所创建的全部文件与目录。

## Requirements

1. 支持 `oca-tool uninstall` 命令调用
2. 检测当前目录是否存在 `.opencode/`，若不存在则提示"未找到已安装的 agent 环境"并退出
3. 列出将删除的所有内容（`.opencode/`、`.agents/`、`agent-pyproject.toml`、`agent-package.json`）
4. 确认提示中包含醒目的危险操作警告标识
5. 用户确认后才执行删除，否则退出
6. 删除每个项目后输出状态信息
7. 无参数（uninstall 不需要预设选择）

## Architecture

### Project Structure Changes

```
src/oca_tool/
├── cli.py              # +uninstall 子命令注册与分发
├── uninstaller.py      # +新建，核心逻辑
├── installer.py        # 不变
└── ...
tests/
├── test_installer.py   # 不变
└── test_uninstaller.py # +新建，uninstall 测试
```

### CLI Changes (`cli.py`)

新增 `uninstall` 子解析器（无参数），在 `if/elif` 链中添加分发：

```
subparsers.add_parser("uninstall", help="卸载 agent 环境")
```

### Uninstaller Module (`uninstaller.py`)

#### `uninstall() -> None`

主流程函数，无参数（操作当前工作目录）：

```
oca-tool uninstall
  │
  ├─ 1. 检测 .opencode/ 是否存在？
  │     ├─ 不存在 → print("未找到已安装的 agent 环境") → exit(0)
  │     └─ 存在 → continue
  │
  ├─ 2. 构建待删除清单
  │     ├─ .opencode/           (目录)
  │     ├─ .agents/             (目录，若存在)
  │     ├─ agent-pyproject.toml (文件，若存在)
  │     └─ agent-package.json   (文件，若存在)
  │
  ├─ 3. 显示危险操作警告 + 清单
  │     ⚠️ 危险操作！即将永久删除以下内容：
  │        • .opencode/       — agent 配置目录
  │        • .agents/         — agent 定义目录
  │        • agent-pyproject.toml  — Python 依赖配置
  │        • agent-package.json    — Node 依赖配置
  │     此操作不可撤销！确定要执行吗？[y/N]
  │
  ├─ 4. 用户确认？
  │     ├─ yes → continue
  │     └─ no  → exit(0)
  │
  └─ 5. 逐个删除并输出状态
        ├─ rm .opencode/ ...
        ├─ rm .agents/ ...
        ├─ rm agent-pyproject.toml ...
        └─ rm agent-package.json ...
```

### Error Handling

- `.opencode/` 不存在：提示后正常退出（exit code 0）
- 无确认：不进行任何删除操作
- 删除失败（权限等）：报告具体错误，继续尝试删除其余项目，最后以非零退出码退出
- 部分不存在的情景：清单仅包含实际存在的项目，不报错

### Files Referenced

| 路径 | 类型 | 说明 |
|---|---|---|
| `.opencode/` | 目录 | install 创建的 agent 配置目录 |
| `.agents/` | 目录 | 从 `.opencode/.agents/` 移出的 agent 定义 |
| `agent-pyproject.toml` | 文件 | 从 `.opencode/` 移出的 Python 依赖配置 |
| `agent-package.json` | 文件 | 从 `.opencode/` 移出的 Node 依赖配置 |

## Out of Scope

- 不卸载由 `uv sync` / `bun install` 创建的虚拟环境或 `node_modules`（这些由包管理器自身管理）
- 不提供选择性删除（避免增加复杂性，用户可手动操作）
