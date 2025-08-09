# tests/unit/test_manager.py
import pytest
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

from claude_artifact_manager.manager import ArtifactManager

@pytest.fixture
def mock_npm_install(monkeypatch):
    """A more sophisticated mock for subprocess.run that simulates npm install."""

    def custom_side_effect(*args, **kwargs):
        command_str = args[0]
        cwd = Path(kwargs.get("cwd"))

        if "npm install" in command_str:
            pkg_path = cwd / "package.json"
            if pkg_path.exists():
                pkg_data = json.loads(pkg_path.read_text())

                # Simulate adding the installed deps to package.json
                deps_to_add = command_str.split("npm install")[1].strip().split(" ")
                if not pkg_data.get("dependencies"):
                    pkg_data["dependencies"] = {}

                for dep in deps_to_add:
                    dep_name = dep.split('@')[0]
                    if dep_name:
                        pkg_data["dependencies"][dep_name] = "latest"

                pkg_path.write_text(json.dumps(pkg_data))

        mock_result = MagicMock(spec=subprocess.CompletedProcess)
        mock_result.returncode = 0
        mock_result.stdout = "Mocked subprocess success"
        mock_result.stderr = ""
        return mock_result

    mock_run = MagicMock(side_effect=custom_side_effect)
    monkeypatch.setattr(subprocess, "run", mock_run)
    return mock_run


class TestArtifactManager:

    def test_initialization_creates_directories(self, temp_project_dir):
        project_path = temp_project_dir
        manager = ArtifactManager(project_path)
        assert (project_path / "claude_artifacts").is_dir()
        assert (project_path / "src" / "components" / "ui").is_dir()
        assert (project_path / "public").is_dir()

    def test_setup_project_basic_flow(self, temp_project_dir):
        # This test uses a more focused mock for subprocess.run
        mock_run = MagicMock()

        def custom_side_effect(*args, **kwargs):
            command_str = args[0]
            cwd = Path(kwargs.get("cwd"))
            if "npm init" in command_str:
                (cwd / "package.json").write_text('{"name": "test-project"}')
            elif "npx tailwindcss init" in command_str:
                (cwd / "tailwind.config.js").write_text("module.exports = {};")

            mock_result = MagicMock(spec=subprocess.CompletedProcess)
            mock_result.returncode = 0
            return mock_result

        mock_run.side_effect = custom_side_effect

        manager = ArtifactManager(temp_project_dir)
        manager.run_command = mock_run # Directly mock the instance's method
        manager.create_base_files = MagicMock() # Mock this to isolate setup_project

        manager.setup_project()

        assert (temp_project_dir / "vite.config.js").is_file()
        assert (temp_project_dir / "tailwind.config.js").is_file()

        pkg_data = json.loads((temp_project_dir / "package.json").read_text())
        assert "dev" in pkg_data["scripts"]

        manager.create_base_files.assert_called_once()

    def test_create_base_files_creates_expected_structure(self, temp_project_dir):
        manager = ArtifactManager(temp_project_dir)
        manager.create_base_files()

        assert (temp_project_dir / "index.html").is_file()
        assert (temp_project_dir / "src" / "main.jsx").is_file()
        assert (temp_project_dir / "src" / "App.jsx").is_file()
        assert (temp_project_dir / "src" / "lib" / "utils.js").is_file()
        assert (temp_project_dir / "src" / "components" / "ui" / "card.jsx").is_file()

    def test_scan_artifacts_uses_cache(self, temp_project_dir, mock_npm_install, capsys):
        project_path = temp_project_dir
        (project_path / "src").mkdir(exist_ok=True)
        manager = ArtifactManager(project_path)

        (project_path / "package.json").write_text(json.dumps({"name": "test-project"}))

        artifacts_dir = project_path / "claude_artifacts"
        (artifacts_dir / "artifact1.jsx").write_text("import React from 'react';")
        (artifacts_dir / "artifact2.jsx").write_text("import 'new-dependency';")

        # --- First scan ---
        manager.scan_artifacts()

        captured = capsys.readouterr()
        assert "Processed 2 files" in captured.out
        assert "used cache for 0 files" in captured.out

        # Check that the first set of dependencies were installed
        first_call_args = mock_npm_install.call_args_list[0][0][0]
        assert "react" in first_call_args and "new-dependency" in first_call_args

        # --- Second scan (should use cache) ---
        (artifacts_dir / "artifact3.jsx").write_text("import 'another-dep';")

        manager.scan_artifacts()

        captured = capsys.readouterr()
        assert "Processed 1 files" in captured.out
        assert "used cache for 2 files" in captured.out

        # Check that only the new dependency was installed
        last_call_args = mock_npm_install.call_args_list[-1][0][0]
        assert "another-dep" in last_call_args
        assert "react" not in last_call_args
        assert "new-dependency" not in last_call_args

        manifest_path = project_path / "public" / "claude_artifacts_manifest.json"
        assert manifest_path.is_file()
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
            assert len(manifest_data) == 3

    def test_update_dependencies_installs_new_deps_batched(self, temp_project_dir, mock_npm_install):
        project_path = temp_project_dir
        manager = ArtifactManager(project_path)

        initial_deps = {"existing-dep": "1.0.0"}
        (manager.package_json).write_text(json.dumps({"name": "test-project", "dependencies": initial_deps}))

        required_deps = {"new-dep1", "new-dep2", "existing-dep", "clsx"}
        manager.update_dependencies(required_deps)

        install_command = mock_npm_install.call_args[0][0]
        assert "new-dep1" in install_command
        assert "new-dep2" in install_command
        assert "clsx" not in install_command # It's a base dependency, should not be installed
        assert "existing-dep" not in install_command
