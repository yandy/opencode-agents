import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="oca-tool",
        description="基于 opencode 的 agent 环境搭建工具",
    )
    subparsers = parser.add_subparsers(dest="command")

    install_parser = subparsers.add_parser("install", help="搭建 agent 环境")
    install_parser.add_argument("name", help="agent 名称")

    args = parser.parse_args()

    if args.command == "install":
        from oca_tool.installer import install

        install(args.name)
    else:
        parser.print_help()
