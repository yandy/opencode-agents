# oca-tool Design Spec

## Overview

`oca-tool` 是一个基于 opencode 的 agent 环境搭建 CLI 工具。用户通过 `oca-tool install <agent-name>` 在当前项目中一键生成完整的 opencode agent 环境。

## Requirements

1. 通过 `uv tool install git-repo-url` 安装，安装后拥有 `oca-tool` 命令
2. 支持 `-h/--help` 打印帮助信息
3. 支持 `install <agent-name>` 搭建 agent 环境
4. 不依赖外部 git 仓库

## Architecture

### Project Structure

```
opencode-agents/
├── pyproject.toml              # 项目配置，[project.scripts] 定义 oca-tool
├── src/
│   └── oca_tool/
│       ├── __init__.py
│       ├── __main__.py         # python -m oca_tool 入口
│       ├── cli.py              # argparse 命令定义
│       ├── installer.py        # 环境搭建核心逻辑
│       └── templates/          # 各预置的完整模板
│           ├── office/         # office agent 环境
│           │   ├── opencode.json
│           │   ├── pyproject.toml
│           │   ├── jsproject.json
│           │   ├── system-deps.txt      # 系统级依赖包名列表
│           │   ├── agents/
│           │   │   └── .gitkeep
│           │   ├── .agents/
│           │   │   └── skills/
│           │   │       └── .gitkeep
│           │   └── skills-lock.json
│           ├── research/       # research agent 环境
│           │   ├── opencode.json
│           │   ├── pyproject.toml
│           │   ├── jsproject.json
│           │   ├── system-deps.txt
│           │   ├── agents/
│           │   │   └── web-search.md
│           │   ├── .agents/
│           │   │   └── skills/
│           │   │       └── .gitkeep
│           │   └── skills-lock.json
│           └── default/        # 最小化默认模板
│               ├── opencode.json
│               ├── pyproject.toml
│               ├── jsproject.json
│               ├── system-deps.txt
│               ├── agents/
│               │   └── .gitkeep
│               ├── .agents/
│               │   └── skills/
│               │       └── .gitkeep
│               └── skills-lock.json
```

### Component Responsibilities

#### `cli.py`
- 定义 argparse 命令行接口
- 命令: `oca-tool -h / --help`, `oca-tool install <agent-name>`
- 解析参数后调用 `installer.py`

#### `installer.py`
- `match_preset(name: str) -> str`: 根据 agent-name 匹配模板目录名
  - 包含 "office" → `office`
  - 包含 "research" → `research`
  - 其他 → `default`
- `check_existing() -> bool`: 检查 `.opencode` 是否已存在
- `confirm_overwrite() -> bool`: 询问用户是否覆盖
- `copy_template(preset: str)`: 将模板目录拷贝到 `.opencode/`
- `create_symlinks()`: 创建符号链接
  - `pyproject.toml -> .opencode/pyproject.toml`
  - `package.json -> .opencode/jsproject.json`
  - `.opencode/skills -> .opencode/.agents/skills/`
- `prompt_install_deps()`: 询问是否运行 `uv sync` 和 `bun install`
- `install_deps()`: 执行 `uv sync` 和 `bun install`
- `print_system_deps()`: 读取 `.opencode/system-deps.txt`，按 apt/dnf/pacman 格式输出安装提示

#### `system-deps.txt`
每个模板目录下包含一个 `system-deps.txt` 文件，每行一个系统包名。install 完成后，installer 读取此文件并向用户输出多行安装提示：

```
根据你的系统运行对应命令安装系统依赖:
  apt-get install <pkg1> <pkg2> ...
  dnf install <pkg1> <pkg2> ...
  pacman -Sy <pkg1> <pkg2> ...
```

若文件为空或不存在则跳过此步骤。

### Install Flow

```
oca-tool install <agent-name>
  │
  ├─ 1. match_preset(agent-name) → preset_name
  ├─ 2. check_existing() ?
  │     ├─ exists → confirm_overwrite() ?
  │     │     ├─ yes → continue
  │     │     └─ no → exit
  │     └─ not exists → continue
  ├─ 3. copy_template(preset_name)
  ├─ 4. create_symlinks()
  │     ├─ ln -s .opencode/pyproject.toml pyproject.toml
  │     ├─ ln -s .opencode/jsproject.json package.json
  │     └─ ln -s .opencode/.agents/skills .opencode/skills
  ├─ 5. prompt_install_deps() ?
  │     ├─ yes → install_deps() (uv sync, bun install)
  │     └─ no → skip
  └─ 6. print_system_deps()
        └─ 读取 .opencode/system-deps.txt，输出各包管理器安装命令
```
```

### Preset Templates

#### office
- 文档处理 agent 环境
- Python 依赖: markitdown, openpyxl, pandas, pdf2image, pdfplumber, pillow, pytesseract, pypdf, reportlab
- JS 依赖: docx, pdf-lib, pptxgenjs
- 系统依赖: qpdf (system-deps.txt 中列出)
- 不含 web-search agent
- Python >= 3.12

#### research
- 搜索研究 agent 环境
- Python 依赖: 同 office
- JS 依赖: 同 office
- 系统依赖: qpdf (system-deps.txt 中列出)
- 包含 web-search.md agent
- opencode.json 设置 `default_agent: "plan"`
- Python >= 3.12

#### default
- 最小化模板
- Python 依赖: markitdown（基础文档处理）
- JS 依赖: 无（jsproject.json 中 dependencies 为空对象）
- 空的 agents/ 目录
- 不含 skills
- 系统依赖: 无（system-deps.txt 为空）
- Python >= 3.12

### pyproject.toml (this project)

```toml
[project]
name = "oca-tool"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[project.scripts]
oca-tool = "oca_tool.cli:main"

[build-system]
requires = ["hatchling"]
build-path = "src"
```

### Error Handling

- `.opencode` 已存在: 询问用户覆盖、合并或取消
- `uv sync` 失败: 提示用户手动运行
- `bun install` 失败: 提示用户手动运行
- 符号链接创建失败: 报告错误并退出
- 模板拷贝失败: 报告错误并退出

### Extensibility

新增预置配置只需:
1. 在 `templates/` 下创建新目录，放入完整的 agent 环境文件
2. 在 `installer.py` 的 `match_preset()` 函数中添加匹配规则

## Out of Scope

- 不提供已有 agent 环境的升级/迁移功能
- 不管理 opencode 本身的安装
- 不管理 API key 配置
