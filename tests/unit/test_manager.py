# tests/unit/test_manager.py
import pytest
import json
import subprocess
import os
from pathlib import Path
from unittest.mock import MagicMock, call, ANY # ANY can be useful for some args

from claude_artifact_manager.manager import ArtifactManager

class TestArtifactManager:

    def test_initialization_creates_directories(self, temp_project_dir):
        project_path = temp_project_dir
        # Note: ArtifactManager constructor itself creates claude_artifacts, ui_dir, public_dir
        # It does NOT call create_base_files(), so src/lib and src won't exist yet
        # unless their parent (src) is created by ui_dir.mkdir(parents=True)
        manager = ArtifactManager(project_path)

        assert (project_path / "claude_artifacts").is_dir()
        assert (project_path / "src" / "components" / "ui").is_dir() # This will create src/components as well
        assert (project_path / "public").is_dir()
        assert (project_path / "src").is_dir() # Check if src was created by ui_dir

        # These are created by create_base_files, not by __init__
        # So they should not exist yet, or this test needs to call create_base_files
        # assert (project_path / "src" / "lib").exists()


    def test_setup_project_basic_flow(self, temp_project_dir, mock_subprocess_run):
        project_path = temp_project_dir
        manager = ArtifactManager(project_path)
        manager.create_base_files = MagicMock()

        # This side effect simulates the file creations that the real commands would do
        def setup_side_effect(*args, **kwargs):
            command = args[0]
            cwd = kwargs.get("cwd", project_path)

            if "npm init -y" in command:
                (cwd / "package.json").write_text(json.dumps({"name": "test-proj", "scripts": {}}))

            if "tailwindcss" in command and "init" in command:
                tailwind_content = """
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [],
  theme: {
    extend: {},
  },
  plugins: [],
}
"""
                (cwd / "tailwind.config.js").write_text(tailwind_content)
                (cwd / "postcss.config.js").write_text("module.exports = {};")

            mock_result = MagicMock(spec=subprocess.CompletedProcess)
            mock_result.returncode = 0
            mock_result.stdout = "Mocked subprocess success"
            mock_result.stderr = ""
            return mock_result

        mock_subprocess_run.side_effect = setup_side_effect

        manager.setup_project()

        mock_subprocess_run.assert_any_call("npm init -y", check=True, capture_output=True, text=True, shell=True, cwd=project_path)

        # Check that the tailwindcss init command was called
        tailwindcss_cli_path = os.path.join(".", "node_modules", "tailwindcss", "lib", "cli.js")
        expected_tailwind_cmd = f"node {tailwindcss_cli_path} init -p"

        found_tailwind_call = False
        for actual_call in mock_subprocess_run.call_args_list:
            if expected_tailwind_cmd in str(actual_call):
                found_tailwind_call = True
                break
        assert found_tailwind_call, f"Call to initialize tailwindcss ('{expected_tailwind_cmd}') was not found."

        assert (project_path / "vite.config.js").is_file()

        tailwind_config_path = project_path / "tailwind.config.js"
        assert tailwind_config_path.is_file()
        tailwind_content = tailwind_config_path.read_text()
        assert 'content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"]' in tailwind_content

        pkg_json_path = project_path / "package.json"
        assert pkg_json_path.is_file()
        with open(pkg_json_path, 'r') as f:
            pkg_data = json.load(f)
            assert "dev" in pkg_data["scripts"]
            assert pkg_data["scripts"]["dev"] == "vite"

        manager.create_base_files.assert_called_once()


    def test_create_base_files_creates_expected_structure(self, temp_project_dir):
        # This test needs access to template files.
        # In a real test environment, you might need to ensure that importlib.resources
        # can find these files, which might mean running pytest from the repo root
        # or adjusting PYTHONPATH. For now, assume they are findable.
        manager = ArtifactManager(temp_project_dir)
        manager.create_base_files()

        assert (temp_project_dir / "index.html").is_file()
        assert (temp_project_dir / "src" / "main.jsx").is_file()
        assert (temp_project_dir / "src" / "App.jsx").is_file()
        assert (temp_project_dir / "src" / "index.css").is_file()
        assert (temp_project_dir / "src" / "lib" / "utils.js").is_file()

        # Check a couple of UI files (assuming card.jsx and button.jsx are in templates)
        ui_dir = temp_project_dir / "src" / "components" / "ui"
        assert (ui_dir / "card.jsx").is_file()
        assert (ui_dir / "button.jsx").is_file()

        # Verify content of a small critical file (e.g., index.html)
        index_html_content = (temp_project_dir / "index.html").read_text()
        assert '<script type="module" src="/src/main.jsx"></script>' in index_html_content


    def test_scan_artifacts_identifies_deps_and_creates_manifest(self, temp_project_dir, mock_subprocess_run):
        project_path = temp_project_dir
        manager = ArtifactManager(project_path)

        # Create dummy package.json for update_dependencies to read
        # This is important as update_dependencies is called by scan_artifacts
        with open(project_path / "package.json", "w") as f:
            json.dump({"name": "test-project", "version": "0.1.0", "dependencies": {}}, f)

        artifacts_dir = project_path / "claude_artifacts"
        # artifacts_dir is created by ArtifactManager.__init__
        # artifacts_dir.mkdir() # Not needed

        artifact1_content = "import React from 'react'; export default () => <div />;"
        (artifacts_dir / "artifact1.jsx").write_text(artifact1_content)

        artifact2_content = "import { someUtil } from 'new-dependency'; export default () => <div />;"
        (artifacts_dir / "artifact2.jsx").write_text(artifact2_content)

        # Artifact with a dependency already in base_dependencies (e.g. clsx)
        artifact3_content = "import clsx from 'clsx'; export default () => <div />;"
        (artifacts_dir / "artifact3.jsx").write_text(artifact3_content)

        found_artifacts = manager.scan_artifacts()

        assert len(found_artifacts) == 3
        assert any(a['name'] == 'Artifact1' for a in found_artifacts)
        assert any(a['name'] == 'Artifact2' for a in found_artifacts)
        assert any(a['name'] == 'Artifact3' for a in found_artifacts)

        manifest_path = project_path / "public" / "claude_artifacts_manifest.json"
        assert manifest_path.is_file()
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
            assert len(manifest_data) == 3
            # Order might not be guaranteed, so check for existence
            assert any(item['id'] == 'artifact1' for item in manifest_data)
            assert any(item['id'] == 'artifact2' for item in manifest_data)


        # Check if update_dependencies (called by scan_artifacts) tried to install "new-dependency"
        mock_subprocess_run.assert_any_call("npm install new-dependency@latest", cwd=project_path, check=True, capture_output=True, text=True, shell=True)

        # Ensure clsx (from base_dependencies) was not installed again
        clsx_install_call = call("npm install clsx@latest", cwd=project_path, check=True, capture_output=True, text=True, shell=True)
        assert clsx_install_call not in mock_subprocess_run.call_args_list


    def test_update_dependencies_installs_new_deps(self, temp_project_dir, mock_subprocess_run):
        project_path = temp_project_dir
        manager = ArtifactManager(project_path)

        # Create package.json with some existing dependencies
        initial_deps = {"existing-dep": "1.0.0"}
        with open(manager.package_json, "w") as f:
            json.dump({"name": "test-project", "dependencies": initial_deps}, f)

        required_deps = {"new-dep1", "existing-dep", "clsx"} # clsx is a base_dependency

        manager.update_dependencies(required_deps)

        # Should install new-dep1
        mock_subprocess_run.assert_any_call("npm install new-dep1@latest", cwd=project_path, check=True, capture_output=True, text=True, shell=True)

        # Should NOT try to install existing-dep or clsx (which is a base dep)
        # Check that a call for 'existing-dep' was NOT made
        found_existing_dep_call = False
        for actual_call in mock_subprocess_run.call_args_list:
            command_args = actual_call[0][0]
            if "npm install existing-dep@latest" in command_args:
                found_existing_dep_call = True
                break
        assert not found_existing_dep_call, "Should not try to install already existing dependency 'existing-dep'."

        found_clsx_call = False
        for actual_call in mock_subprocess_run.call_args_list:
            command_args = actual_call[0][0]
            if "npm install clsx@latest" in command_args:
                found_clsx_call = True
                break
        assert not found_clsx_call, "Should not try to install base dependency 'clsx' again."

