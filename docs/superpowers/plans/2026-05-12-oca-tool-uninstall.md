# oca-tool uninstall Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `oca-tool uninstall` command that safely removes all files/directories created by `oca-tool install`.

**Architecture:** Follow existing CLI pattern: add `uninstall` subparser in `cli.py`, implement core logic in `uninstaller.py` as standalone functions, test with pytest + monkeypatch + tmpdir.

**Tech Stack:** Python 3.12+, argparse, pathlib, shutil, pytest

---

## Git Branch Setup

- [ ] **Step 0: Create and switch to a feature branch**

```bash
git checkout -b feat/uninstall-command
```

Expected: Switched to a new branch `feat/uninstall-command`

---

### Task 1: Write failing tests for uninstaller

**Files:**
- Create: `tests/test_uninstaller.py`

- [ ] **Step 1: Write tests for `uninstall()` when no `.opencode/` exists**

```python
import os
from pathlib import Path

from oca_tool.uninstaller import uninstall


class TestUninstallNoEnvironment:
    def test_no_opencode_prints_message(self, capsys):
        uninstall()
        captured = capsys.readouterr()
        assert "未找到已安装的 agent 环境" in captured.out
```

Run: `pytest tests/test_uninstaller.py::TestUninstallNoEnvironment::test_no_opencode_prints_message -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'oca_tool.uninstaller'`

- [ ] **Step 2: Write tests for confirmation flow and deletion**

```python
class TestUninstallConfirmation:
    def test_cancel_does_not_delete(self, tmp_path, monkeypatch):
        dot_opencode = tmp_path / ".opencode"
        dot_opencode.mkdir()
        agents_dir = tmp_path / ".agents"
        agents_dir.mkdir()
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("")
        package_json = tmp_path / "package.json"
        package_json.write_text("")

        monkeypatch.setattr("builtins.input", lambda prompt="": "n")
        monkeypatch.chdir(tmp_path)
        uninstall()

        assert dot_opencode.exists()
        assert agents_dir.exists()
        assert pyproject.exists()
        assert package_json.exists()

    def test_confirm_deletes_all(self, tmp_path, monkeypatch):
        dot_opencode = tmp_path / ".opencode"
        dot_opencode.mkdir()
        agents_dir = tmp_path / ".agents"
        agents_dir.mkdir()
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("")
        package_json = tmp_path / "package.json"
        package_json.write_text("")

        monkeypatch.setattr("builtins.input", lambda prompt="": "y")
        monkeypatch.chdir(tmp_path)
        uninstall()

        assert not dot_opencode.exists()
        assert not agents_dir.exists()
        assert not pyproject.exists()
        assert not package_json.exists()

    def test_confirm_deletes_partial(self, tmp_path, monkeypatch):
        dot_opencode = tmp_path / ".opencode"
        dot_opencode.mkdir()

        monkeypatch.setattr("builtins.input", lambda prompt="": "y")
        monkeypatch.chdir(tmp_path)
        uninstall()

        assert not dot_opencode.exists()

    def test_shows_danger_warning(self, tmp_path, monkeypatch, capsys):
        dot_opencode = tmp_path / ".opencode"
        dot_opencode.mkdir()

        monkeypatch.setattr("builtins.input", lambda prompt="": "y")
        monkeypatch.chdir(tmp_path)
        uninstall()
        captured = capsys.readouterr()
        assert "⚠️" in captured.out
        assert "危险操作" in captured.out

    def test_uninstall_prints_status(self, tmp_path, monkeypatch, capsys):
        dot_opencode = tmp_path / ".opencode"
        dot_opencode.mkdir()

        monkeypatch.setattr("builtins.input", lambda prompt="": "y")
        monkeypatch.chdir(tmp_path)
        uninstall()
        captured = capsys.readouterr()
        assert "已删除" in captured.out
```

- [ ] **Step 3: Run all tests to verify they fail**

Run: `pytest tests/test_uninstaller.py -v`
Expected: All tests FAIL (import error for uninstaller module, or function not defined)

- [ ] **Step 4: Commit**

```bash
git add tests/test_uninstaller.py
git commit -m "test: add failing tests for oca-tool uninstall"
```

---

### Task 2: Implement uninstaller.py

**Files:**
- Create: `src/oca_tool/uninstaller.py`

- [ ] **Step 1: Create `uninstaller.py` with core logic**

```python
import shutil
import sys
from pathlib import Path


ITEMS: list[tuple[str, str, str]] = [
    (".opencode", "目录", "agent 配置目录"),
    (".agents", "目录", "agent 定义目录"),
    ("pyproject.toml", "文件", "Python 依赖配置"),
    ("package.json", "文件", "Node 依赖配置"),
]


def _list_items(target: Path) -> list[tuple[Path, str, str]]:
    result: list[tuple[Path, str, str]] = []
    for name, kind, desc in ITEMS:
        path = target / name
        if path.exists() or path.is_symlink():
            result.append((path, kind, desc))
    return result


def _confirm(prompt: str) -> bool:
    answer = input(f"{prompt} [y/N] ").strip().lower()
    return answer in ("y", "yes")


def uninstall() -> None:
    target = Path.cwd()
    dot_opencode = target / ".opencode"

    if not dot_opencode.exists():
        print("未找到已安装的 agent 环境。")
        return

    items = _list_items(target)

    print()
    print("⚠️ 危险操作！即将永久删除以下内容：")
    for path, kind, desc in items:
        suffix = "/" if kind == "目录" else ""
        print(f"   • {path.name}{suffix}  — {desc}")
    print("此操作不可撤销！")

    if not _confirm("确定要执行吗"):
        print("已取消。")
        return

    for path, kind, desc in items:
        try:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"已删除: {path.name}")
        except OSError as e:
            print(f"删除失败: {path.name} - {e}", file=sys.stderr)
            sys.exit(1)
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/test_uninstaller.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add src/oca_tool/uninstaller.py
git commit -m "feat: add uninstaller module for oca-tool uninstall"
```

---

### Task 3: Register uninstall command in CLI

**Files:**
- Modify: `src/oca_tool/cli.py`

- [ ] **Step 1: Add `uninstall` subparser and dispatch**

Modify `cli.py` to add uninstall subparser and dispatch:

```python
import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="oca-tool",
        description="基于 opencode 的 agent 环境搭建工具",
    )
    subparsers = parser.add_subparsers(dest="command")

    install_parser = subparsers.add_parser("install", help="搭建 agent 环境")
    install_parser.add_argument("name", help="agent 名称")

    subparsers.add_parser("uninstall", help="卸载 agent 环境")

    args = parser.parse_args()

    if args.command == "install":
        from oca_tool.installer import install

        install(args.name)
    elif args.command == "uninstall":
        from oca_tool.uninstaller import uninstall

        uninstall()
    else:
        parser.print_help()
```

- [ ] **Step 2: Run all tests**

Run: `pytest tests/ -v`
Expected: All existing tests + new uninstall tests PASS

- [ ] **Step 3: Manual smoke test**

```bash
# Create a temp dir, install an agent, then uninstall it
tmpdir=$(mktemp -d)
cd "$tmpdir"
oca-tool install test-agent
# (confirm, select model, cancel deps)
ls -la
oca-tool uninstall
# Should show warning, confirm with 'y', then clean up
ls -la .opencode 2>&1 || echo "cleaned up"
cd /
rm -rf "$tmpdir"
```

- [ ] **Step 4: Commit**

```bash
git add src/oca_tool/cli.py
git commit -m "feat: register uninstall command in CLI"
```

---

## Git Branch Completion

- [ ] **Step 1: Verify branch state**

```bash
git log --oneline
git status
```

Expected: All 3 commits on `feat/uninstall-command` branch, working tree clean

- [ ] **Step 2: Push branch to remote**

```bash
git push -u origin feat/uninstall-command
```

Expected: Remote branch created, tracking set up
