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
