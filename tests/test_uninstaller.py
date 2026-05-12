import os
from pathlib import Path

from oca_tool.uninstaller import uninstall


class TestUninstallNoEnvironment:
    def test_no_opencode_prints_message(self, capsys):
        uninstall()
        captured = capsys.readouterr()
        assert "未找到已安装的 agent 环境" in captured.out


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
