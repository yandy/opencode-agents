我想做一个 基于opencode 的agent构建工具，效果如下：

1. 可以通过 uv tool install git-repo-url 安装，安装后拥有一个命令： `oca-tool`
2. `oca-tool` 命令使用方式如下：

| 命令 | 效果 |
|--- |---|
| `oca-tool -h / --help` | 打印帮助信息 |
| `oca-tool install <agent-name>` | 给当前项目搭建名为 `<agent-name>` 的agent环境|

3. 以下是2个repo各包含名为 `office-agent` 和 `research-agent` 的agent环境的构建说明：

- [office-agent](https://github.com/yandy/office-agent)
- [research-agent](https://github.com/yandy/research-agent)

4. 要求完成本项目开发以后，不依赖于 上述两个git repo
