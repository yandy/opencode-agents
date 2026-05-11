import os
import tempfile
from pathlib import Path

from oca_tool.installer import match_preset, _parse_system_deps


class TestMatchPreset:
    def test_office_lowercase(self):
        assert match_preset("office") == "office"

    def test_office_uppercase(self):
        assert match_preset("OFFICE") == "office"

    def test_office_contains(self):
        assert match_preset("my-office-agent") == "office"

    def test_research_lowercase(self):
        assert match_preset("research") == "research"

    def test_research_contains(self):
        assert match_preset("my-research-tool") == "research"

    def test_default_random(self):
        assert match_preset("random-name") == "default"

    def test_default_empty(self):
        assert match_preset("") == "default"


class TestParseSystemDeps:
    def test_parse_normal(self):
        content = "[apt]\nqpdf\n\n[dnf]\nqpdf\n\n[pacman]\nqpdf\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            deps = _parse_system_deps(Path(path))
            assert deps == {"apt": ["qpdf"], "dnf": ["qpdf"], "pacman": ["qpdf"]}
        finally:
            os.unlink(path)

    def test_parse_empty_sections(self):
        content = "[apt]\n\n[dnf]\n\n[pacman]\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            deps = _parse_system_deps(Path(path))
            assert deps == {"apt": [], "dnf": [], "pacman": []}
        finally:
            os.unlink(path)

    def test_parse_multiple_packages(self):
        content = "[apt]\nqpdf\npoppler-utils\n\n[pacman]\nqpdf\npoppler\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            deps = _parse_system_deps(Path(path))
            assert deps == {"apt": ["qpdf", "poppler-utils"], "pacman": ["qpdf", "poppler"]}
        finally:
            os.unlink(path)

    def test_parse_nonexistent_file(self):
        deps = _parse_system_deps(Path("/nonexistent/path.conf"))
        assert deps == {}

    def test_parse_empty_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("")
            path = f.name
        try:
            deps = _parse_system_deps(Path(path))
            assert deps == {}
        finally:
            os.unlink(path)


class TestInstallIntegration:
    def test_install_office_creates_opencode_dir(self):
        import oca_tool.installer as installer_mod
        import tempfile, os
        original_confirm = installer_mod._confirm
        installer_mod._confirm = lambda prompt: False
        original_cwd = os.getcwd()

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                from oca_tool.installer import install

                install("test-office-agent")
                dot_opencode = Path(tmpdir) / ".opencode"

                assert dot_opencode.is_dir()
                assert (dot_opencode / "opencode.json").is_file()
                assert (dot_opencode / "pyproject.toml").is_file()
                assert (dot_opencode / "jsproject.json").is_file()
                assert (dot_opencode / "system-deps.conf").is_file()
                assert (dot_opencode / "skills-lock.json").is_file()
                assert (dot_opencode / "agents").is_dir()
                assert (dot_opencode / ".agents" / "skills").is_dir()

                pyproject = Path(tmpdir) / "pyproject.toml"
                assert pyproject.is_symlink()

                package_json = Path(tmpdir) / "package.json"
                assert package_json.is_symlink()

                skills = dot_opencode / "skills"
                assert skills.is_symlink()
            finally:
                installer_mod._confirm = original_confirm
                os.chdir(original_cwd)

    def test_install_research_has_web_search(self):
        import oca_tool.installer as installer_mod
        import tempfile, os
        original_confirm = installer_mod._confirm
        installer_mod._confirm = lambda prompt: False
        original_cwd = os.getcwd()

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                from oca_tool.installer import install

                install("research-tool")
                dot_opencode = Path(tmpdir) / ".opencode"

                assert (dot_opencode / "agents" / "web-search.md").is_file()
            finally:
                installer_mod._confirm = original_confirm
                os.chdir(original_cwd)

    def test_install_default_minimal(self):
        import oca_tool.installer as installer_mod
        import tempfile, os
        original_confirm = installer_mod._confirm
        installer_mod._confirm = lambda prompt: False
        original_cwd = os.getcwd()

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                from oca_tool.installer import install

                install("xyz")
                dot_opencode = Path(tmpdir) / ".opencode"

                assert dot_opencode.is_dir()
                assert not (dot_opencode / "agents" / "web-search.md").exists()
            finally:
                installer_mod._confirm = original_confirm
                os.chdir(original_cwd)

    def test_install_office_without_web_search(self):
        import oca_tool.installer as installer_mod
        import tempfile, os
        original_confirm = installer_mod._confirm
        installer_mod._confirm = lambda prompt: False
        original_cwd = os.getcwd()

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                from oca_tool.installer import install

                install("my-office-env")
                dot_opencode = Path(tmpdir) / ".opencode"

                assert not (dot_opencode / "agents" / "web-search.md").exists()
            finally:
                installer_mod._confirm = original_confirm
                os.chdir(original_cwd)

    def test_install_overwrite_cancels(self):
        import oca_tool.installer as installer_mod
        import tempfile, os
        original_confirm = installer_mod._confirm
        installer_mod._confirm = lambda prompt: False
        original_cwd = os.getcwd()

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                from oca_tool.installer import install

                install("test")
                dot_opencode = Path(tmpdir) / ".opencode"
                first_stat = dot_opencode.stat()

                install("test")
                assert dot_opencode.stat() == first_stat
            finally:
                installer_mod._confirm = original_confirm
                os.chdir(original_cwd)
