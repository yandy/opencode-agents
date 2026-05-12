import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="oca-tool",
        description="基于 opencode 的 agent 环境搭建工具",
    )
    subparsers = parser.add_subparsers(dest="command")

    install_parser = subparsers.add_parser(
        "install",
        help="搭建 agent 环境",
        description="根据 agent 名称匹配预置模板，在当前项目 .opencode/ 目录生成完整环境文件。",
    )
    install_parser.add_argument(
        "name",
        help="agent 名称（根据名称关键字匹配模板：含 office → 办公模板，含 research → 科研模板，其他 → 默认模板）。"
        " 可用预置模板：default, office, research",
    )

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
