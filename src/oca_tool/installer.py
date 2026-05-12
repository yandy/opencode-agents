import shutil
import subprocess
import sys
from pathlib import Path


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def match_preset(name: str) -> str:
    lower = name.lower()
    if "office" in lower:
        return "office"
    if "research" in lower:
        return "research"
    return "default"


MODEL_PLACEHOLDER = "{{model}}"


def _confirm(prompt: str) -> bool:
    answer = input(f"{prompt} [y/N] ").strip().lower()
    return answer in ("y", "yes")


def _replace_model_placeholder(target_dir: Path, model: str) -> None:
    for file in target_dir.rglob("*"):
        if file.is_file() and not file.is_symlink():
            try:
                content = file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if MODEL_PLACEHOLDER in content:
                file.write_text(content.replace(MODEL_PLACEHOLDER, model), encoding="utf-8")


def _parse_system_deps(conf_path: Path) -> dict[str, list[str]]:
    deps: dict[str, list[str]] = {}
    current_section = ""
    if not conf_path.exists():
        return deps
    for line in conf_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1]
            deps[current_section] = []
        elif current_section:
            deps[current_section].append(line)
    return deps


def install(name: str) -> None:
    target = Path.cwd()
    preset = match_preset(name)
    src = TEMPLATES_DIR / preset
    dot_opencode = target / ".opencode"

    print(f"搭建 agent 环境: {name} (预置: {preset})")

    if dot_opencode.exists():
        if not _confirm(".opencode 目录已存在，是否覆盖?"):
            print("已取消。")
            return
        shutil.rmtree(dot_opencode)

    try:
        shutil.copytree(src, dot_opencode, symlinks=True)
    except Exception as e:
        print(f"拷贝模板失败: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        pyproject_path = target / "pyproject.toml"
        if pyproject_path.exists() or pyproject_path.is_symlink():
            pyproject_path.unlink()
        pyproject_path.symlink_to(".opencode/agent-pyproject.toml")

        package_json = target / "package.json"
        if package_json.exists() or package_json.is_symlink():
            package_json.unlink()
        package_json.symlink_to(".opencode/agent-package.json")

        skills_link = dot_opencode / "skills"
        if skills_link.exists() or skills_link.is_symlink():
            skills_link.unlink()
        skills_link.symlink_to(".agents/skills/", target_is_directory=True)
    except OSError as e:
        print(f"创建符号链接失败: {e}", file=sys.stderr)
        sys.exit(1)

    print("环境文件已创建。")

    if _confirm("是否立即安装 Python 和 JS 依赖? (需要 uv 和 bun)"):
        _install_deps(target)

    _print_system_deps(dot_opencode)


def _install_deps(target: Path) -> None:
    print("运行 uv sync...")
    result = subprocess.run(["uv", "sync"], cwd=target)
    if result.returncode != 0:
        print("uv sync 失败，请手动运行。", file=sys.stderr)

    print("运行 bun install...")
    result = subprocess.run(["bun", "install"], cwd=target)
    if result.returncode != 0:
        print("bun install 失败，请手动运行。", file=sys.stderr)


def _print_system_deps(dot_opencode: Path) -> None:
    conf_path = dot_opencode / "system-deps.conf"
    deps = _parse_system_deps(conf_path)

    has_deps = False
    for pkgs in deps.values():
        if pkgs:
            has_deps = True
            break

    if not has_deps:
        return

    print()
    print("根据你的系统运行对应命令安装系统依赖:")
    for section in ("apt", "dnf", "pacman"):
        pkgs = deps.get(section, [])
        if not pkgs:
            continue
        if section == "apt":
            print(f"  apt-get install {' '.join(pkgs)}")
        elif section == "dnf":
            print(f"  dnf install {' '.join(pkgs)}")
        elif section == "pacman":
            print(f"  pacman -Sy {' '.join(pkgs)}")
