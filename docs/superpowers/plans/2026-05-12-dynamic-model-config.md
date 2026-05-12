# 动态模型配置实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让用户在 `oca-tool install` 时选择模型，替换模板中的 `{{model}}` 占位符。

**Architecture:** 模板中用 `{{model}}` 占位，installer.py 在 `copytree` 后询问用户选择模型，再用 `str.replace` 递归替换所有文件中的占位符。`small_model`、`model`、`agent.explore.model` 三个字段统一替换。

**Tech Stack:** Python 3.12+, 标准库（零外部依赖），pytest 测试。

---

### Task 1: 模板添加 `{{model}}` 占位符 & 删除 web-search.md 的 model 字段

**Files:**
- Modify: `src/oca_tool/templates/office/opencode.json`
- Modify: `src/oca_tool/templates/research/opencode.json`
- Modify: `src/oca_tool/templates/research/agents/web-search.md`

- [ ] **Step 1: office/opencode.json 添加占位符**

将 `model`、`small_model`、`agent.explore.model` 的值改为 `{{model}}`。

```json
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "explore": {
      "model": "{{model}}"
    }
  },
  "model": "{{model}}",
  "small_model": "{{model}}"
}
```

- [ ] **Step 2: research/opencode.json 添加占位符**

同上，修改三个字段为 `{{model}}`。

```json
{
  "$schema": "https://opencode.ai/config.json",
  "default_agent": "plan",
  "agent": {
    "explore": {
      "model": "{{model}}"
    }
  },
  "model": "{{model}}",
  "small_model": "{{model}}"
}
```

- [ ] **Step 3: web-search.md 删除 model 字段**

删除第 4 行 `model: deepseek/deepseek-v4-flash`。

```markdown
---
description: Use this agent when you need to research information on the internet...
mode: subagent
temperature: 0.4
tools:
  read: true
  write: false
  edit: false
  bash: true
  glob: false
  grep: false
  websearch: true
  webfetch: true
---
```

- [ ] **Step 4: Commit**

```bash
git add src/oca_tool/templates/
git commit -m "feat: add {{model}} placeholders, remove web-search.md model field"
```

---

### Task 2: `_replace_model_placeholder()` (TDD)

**Files:**
- Create: `tests/test_installer.py` (追加测试类)
- Modify: `src/oca_tool/installer.py`

- [ ] **Step 1: 写单元测试（RED）**

在 `tests/test_installer.py` 末尾追加 `TestReplaceModelPlaceholder`：

```python
class TestReplaceModelPlaceholder:
    def test_replaces_in_files(self, tmp_path):
        from oca_tool.installer import _replace_model_placeholder
        f = tmp_path / "test.json"
        f.write_text('{"model": "{{model}}"}', encoding="utf-8")
        _replace_model_placeholder(tmp_path, "my-model")
        assert f.read_text(encoding="utf-8") == '{"model": "my-model"}'

    def test_skips_non_matching(self, tmp_path):
        from oca_tool.installer import _replace_model_placeholder
        f = tmp_path / "test.json"
        f.write_text('{"model": "fixed-model"}', encoding="utf-8")
        _replace_model_placeholder(tmp_path, "my-model")
        assert f.read_text(encoding="utf-8") == '{"model": "fixed-model"}'

    def test_replaces_multiple_occurrences(self, tmp_path):
        from oca_tool.installer import _replace_model_placeholder
        f = tmp_path / "test.json"
        f.write_text(
            '{"model": "{{model}}", "small_model": "{{model}}"}',
            encoding="utf-8",
        )
        _replace_model_placeholder(tmp_path, "my-model")
        assert f.read_text(encoding="utf-8") == (
            '{"model": "my-model", "small_model": "my-model"}'
        )
```

- [ ] **Step 2: 确认测试失败（RED）**

Run: `uv run pytest tests/test_installer.py::TestReplaceModelPlaceholder -v`
Expected: FAIL — `_replace_model_placeholder` not defined

- [ ] **Step 3: 写最小实现（GREEN）**

在 `src/oca_tool/installer.py` 的 `_confirm` 之后添加常量和函数：

```python
MODEL_PLACEHOLDER = "{{model}}"


def _replace_model_placeholder(target_dir: Path, model: str) -> None:
    for file in target_dir.rglob("*"):
        if file.is_file():
            content = file.read_text(encoding="utf-8")
            if MODEL_PLACEHOLDER in content:
                file.write_text(content.replace(MODEL_PLACEHOLDER, model), encoding="utf-8")
```

- [ ] **Step 4: 确认测试通过（GREEN）**

Run: `uv run pytest tests/test_installer.py::TestReplaceModelPlaceholder -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add tests/test_installer.py src/oca_tool/installer.py
git commit -m "feat: add _replace_model_placeholder function"
```

---

### Task 3: `_ask_model()` (TDD)

**Files:**
- Modify: `tests/test_installer.py` (追加测试类)
- Modify: `src/oca_tool/installer.py`

- [ ] **Step 1: 写单元测试（RED）**

在 `TestReplaceModelPlaceholder` 之后追加 `TestAskModel`：

```python
class TestAskModel:
    def test_default_model(self, monkeypatch):
        import oca_tool.installer as m
        monkeypatch.setattr("builtins.input", lambda prompt="": "")
        assert m._ask_model() == "minimax-cn-coding-plan/MiniMax-M2.7-highspeed"

    def test_select_first(self, monkeypatch):
        import oca_tool.installer as m
        monkeypatch.setattr("builtins.input", lambda prompt="": "1")
        assert m._ask_model() == "minimax-cn-coding-plan/MiniMax-M2.7-highspeed"

    def test_select_second(self, monkeypatch):
        import oca_tool.installer as m
        monkeypatch.setattr("builtins.input", lambda prompt="": "2")
        assert m._ask_model() == "deepseek/deepseek-v4-flash"

    def test_custom_model(self, monkeypatch):
        import oca_tool.installer as m
        custom = "my-custom/model"
        monkeypatch.setattr("builtins.input", lambda prompt="": custom)
        assert m._ask_model() == custom
```

- [ ] **Step 2: 确认测试失败（RED）**

Run: `uv run pytest tests/test_installer.py::TestAskModel -v`
Expected: FAIL — `_ask_model` not defined

- [ ] **Step 3: 写最小实现（GREEN）**

在 `_replace_model_placeholder` 之后添加：

```python
RECOMMENDED_MODELS = [
    "minimax-cn-coding-plan/MiniMax-M2.7-highspeed",
    "deepseek/deepseek-v4-flash",
]
DEFAULT_MODEL = RECOMMENDED_MODELS[0]


def _ask_model() -> str:
    print()
    print("请选择模型 (输入数字或直接输入自定义模型名称):")
    for i, m in enumerate(RECOMMENDED_MODELS, 1):
        label = " (推荐)" if i == 1 else ""
        print(f"  {i}. {m}{label}")
    while True:
        answer = input(f"输入模型名称 [默认: {DEFAULT_MODEL}]: ").strip()
        if not answer:
            return DEFAULT_MODEL
        if answer in ("1", "2"):
            return RECOMMENDED_MODELS[int(answer) - 1]
        return answer
```

- [ ] **Step 4: 确认测试通过（GREEN）**

Run: `uv run pytest tests/test_installer.py::TestAskModel -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add tests/test_installer.py src/oca_tool/installer.py
git commit -m "feat: add _ask_model function with default/custom selection"
```

---

### Task 4: 将模型选择插入 `install()` 流程 (TDD)

**Files:**
- Modify: `tests/test_installer.py` (集成测试追加断言)
- Modify: `src/oca_tool/installer.py`

- [ ] **Step 1: 写集成测试断言（RED）**

在 `test_install_office_creates_opencode_dir` 的 try 块中，`install()` 调用之后追加：

```python
with open(dot_opencode / "opencode.json") as f:
    import json
    config = json.load(f)
assert config["model"] == "minimax-cn-coding-plan/MiniMax-M2.7-highspeed"
assert config["small_model"] == "minimax-cn-coding-plan/MiniMax-M2.7-highspeed"
assert config["agent"]["explore"]["model"] == "minimax-cn-coding-plan/MiniMax-M2.7-highspeed"
assert "{{model}}" not in (dot_opencode / "opencode.json").read_text()
```

同时在 `test_install_research_has_web_search` 和 `test_install_default_minimal` 中 simlink 断言后追加：

```python
# research: verify model is replaced
with open(dot_opencode / "opencode.json") as f:
    config = json.load(f)
assert config["model"] == "minimax-cn-coding-plan/MiniMax-M2.7-highspeed"
assert "{{model}}" not in (dot_opencode / "opencode.json").read_text()

# default: has no model field
with open(dot_opencode / "opencode.json") as f:
    config = json.load(f)
assert "model" not in config
```

同时每个集成测试需要 mock `_ask_model`，在 mock `_confirm` 的行后添加：

```python
installer_mod._ask_model = lambda: "minimax-cn-coding-plan/MiniMax-M2.7-highspeed"
```

并在 test method 入口保存原值，finally 块恢复：
```python
original_ask_model = installer_mod._ask_model
...
finally:
    installer_mod._ask_model = original_ask_model
```

- [ ] **Step 2: 确认测试失败（RED）**

Run: `uv run pytest tests/test_installer.py::TestInstallIntegration -v`
Expected: FAIL — `{{model}}` 未被替换，模板中仍是字面量

- [ ] **Step 3: 在 `install()` 中加入模型选择（GREEN）**

在 `install()` 中 `copytree` 块之后（第 59 行）、symlink 块之前插入：

```python
    model = _ask_model()
    _replace_model_placeholder(dot_opencode, model)
```

完整流程：
```
1. match_preset
2. copytree
3. ask model + replace placeholder  ← 新增
4. create symlinks
5. confirm & install deps (uv/bun)
6. print system deps
```

- [ ] **Step 4: 确认测试通过（GREEN）**

Run: `uv run pytest tests/test_installer.py::TestInstallIntegration -v`
Expected: PASS

- [ ] **Step 5: 确认全部测试通过**

Run: `uv run pytest tests/ -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add tests/test_installer.py src/oca_tool/installer.py
git commit -m "feat: integrate model selection into install flow"
```

---

### Task 5: 手动验证

- [ ] **Step 1: 创建临时目录，运行安装**

```bash
mkdir -p /tmp/test-oca-install && cd /tmp/test-oca-install && uv run -p /home/yandy/workspace/pri/opencode-agents oca-tool install test-office
```

预期行为：
1. 显示模型选择提示（两个推荐选项 + 自定义输入）
2. 输入 1 或直接回车 → 安装完成
3. `.opencode/opencode.json` 中 model/small_model/agent.explore.model 值正确
4. `.opencode/agents/web-search.md` 中无 model 字段
5. 选择 deepseek → 所有三个字段都是 deepseek

- [ ] **Step 2: 清理**

```bash
rm -rf /tmp/test-oca-install
```
