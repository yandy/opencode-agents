# 动态模型配置 — 安装时询问用户选择模型

## 背景

`oca-tool install` 目前从模板复制静态文件到 `.opencode/` 目录。模板中的模型配置（如 `opencode.json` 的 `model`、`agent.explore.model` 字段）是硬编码的，用户在安装时无法选择。

需求：在安装时询问用户选择模型，将选择结果写入模板。

## 方案

**方法**：字符串替换（`str.replace`）
**理由**：项目零外部依赖（`dependencies = []`），不引入 Jinja2。

### 占位符格式

使用 `{{model}}` 作为占位符。

理由：
- 双花括号不会与 JSON 语法冲突（在 JSON 字符串值中合法）
- 足够独特，不会与真实模型名称碰撞
- 遵循常见模板惯例（Jinja2/Mustache/Handlebars），语义一目了然

### 受影响模板

| 文件 | 字段 | 当前值 | 改为 |
|------|------|--------|------|
| `templates/office/opencode.json` | `model` | `minimax-cn-coding-plan/MiniMax-M2.7-highspeed` | `{{model}}` |
| `templates/office/opencode.json` | `small_model` | `minimax-cn-coding-plan/MiniMax-M2.7-highspeed` | `{{model}}` |
| `templates/office/opencode.json` | `agent.explore.model` | `minimax-cn-coding-plan/MiniMax-M2.7-highspeed` | `{{model}}` |
| `templates/research/opencode.json` | `model` | `minimax-cn-coding-plan/MiniMax-M2.7-highspeed` | `{{model}}` |
| `templates/research/opencode.json` | `small_model` | `minimax-cn-coding-plan/MiniMax-M2.7-highspeed` | `{{model}}` |
| `templates/research/opencode.json` | `agent.explore.model` | `minimax-cn-coding-plan/MiniMax-M2.7-highspeed` | `{{model}}` |

**不替换的字段**：
- `templates/research/agents/web-search.md` 的 `model` — 删除该字段（交由 opencode 自身决定模型）
- `templates/default/opencode.json` — 本身无 model 配置，不变

### 用户交互

在 `installer.py` 的 `install()` 函数中，在 `copytree` 完成后、询问安装依赖前，增加模型选择步骤（即放在现有的第 2 个 `_confirm` 之前）：

```
? 请选择模型 (输入数字或直接输入自定义模型名称):
  1. minimax-cn-coding-plan/MiniMax-M2.7-highspeed (推荐)
  2. deepseek/deepseek-v4-flash
  输入模型名称 [默认: minimax-cn-coding-plan/MiniMax-M2.7-highspeed]:
```

- 显示编号选项（推荐模型放第一项）
- 允许用户输入编号选择，或直接输入完整模型名称
- 直接回车使用默认值
- 输入验证：若输入无效内容（空白、编号超出范围、未知字符串），提示重新输入

### replacement 逻辑

```python
MODEL_PLACEHOLDER = "{{model}}"
RECOMMENDED_MODELS = [
    "minimax-cn-coding-plan/MiniMax-M2.7-highspeed",
    "deepseek/deepseek-v4-flash",
]

def _ask_model() -> str:
    """询问用户选择模型，返回模型名称"""
    ...

def _replace_model_placeholder(target_dir: Path, model: str):
    """递归替换目标目录中所有文件内的 {{model}} 占位符"""
    for file in target_dir.rglob("*"):
        if file.is_file():
            content = file.read_text(encoding="utf-8")
            if MODEL_PLACEHOLDER in content:
                file.write_text(content.replace(MODEL_PLACEHOLDER, model), encoding="utf-8")

def install(name: str):
    ...
    # 1. match_preset
    # 2. copytree
    # 3. NEW: ask model + replace placeholder
    # 4. create symlinks
    # 5. confirm & install deps (uv/bun)
    # 6. print system deps
```

### 测试策略

- 对 `_ask_model()` 做 monkey-patch（沿用 `_confirm` 的 mock 模式）
- 对 `_replace_model_placeholder()` 测试：在临时目录创建含 `{{model}}` 的文件，验证替换结果
- 测试默认值场景和自定义输入场景
