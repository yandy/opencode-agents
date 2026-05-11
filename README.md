# oca-tool

基于 opencode 的 agent 环境搭建工具。

## 安装

```bash
uv tool install git+https://github.com/yandy/opencode-agents.git
```

安装后获得 `oca-tool` 命令。

## 使用

```bash
oca-tool -h                    # 查看帮助
oca-tool install <agent-name>  # 搭建 agent 环境
```

`agent-name` 包含 `office` 或 `research` 时自动匹配对应预置配置，其余名称使用默认模板。

### 预置

| 预置 | 匹配条件 | 包含 |
|------|---------|------|
| office | 名称含 `office` | Python 文档处理依赖、JS 文档生成依赖、系统依赖提示 |
| research | 名称含 `research` | 同上 + web-search agent + `default_agent: plan` |
| default | 未匹配 | 最小化配置，仅含 markitdown |

`install` 执行流程：
1. 将预置模板拷贝到 `.opencode/`
2. 在项目根创建 `pyproject.toml` / `package.json` 符号链接
3. 询问是否运行 `uv sync` / `bun install`
4. 输出系统依赖安装提示

## 开发

```bash
git clone https://github.com/yandy/opencode-agents.git
cd opencode-agents
uv sync
uv run oca-tool -h
```

### 运行测试

```bash
uv run pytest tests/ -v
```

## 系统依赖

部分预置需要系统级软件包。`install` 完成后会输出对应包管理器的安装命令：

```
根据你的系统运行对应命令安装系统依赖:
  apt-get install qpdf
  dnf install qpdf
  pacman -Sy qpdf
```

各预置的系统依赖声明在 `system-deps.conf` 中，以 `[apt]`/`[dnf]`/`[pacman]` 分段。
