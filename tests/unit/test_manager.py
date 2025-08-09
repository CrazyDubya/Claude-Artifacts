# tests/unit/test_manager.py
import pytest
import json
import subprocess
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

        # Mock create_base_files for a more focused unit test
        manager.create_base_files = MagicMock()

        # --- Mock side effects for subprocess ---
        def custom_subprocess_side_effect(*args, **kwargs):
            command_str = args[0]
            cwd = Path(kwargs.get("cwd", project_path))

            if command_str == "npm init -y":
                (cwd / "package.json").write_text('{"name": "test-project"}')
            elif command_str == "npx tailwindcss init -p":
                (cwd / "tailwind.config.js").write_text("module.exports = { content: [], theme: {}, plugins: [] };")
                (cwd / "postcss.config.js").write_text("module.exports = { plugins: {} };")

            mock_result = MagicMock(spec=subprocess.CompletedProcess)
            mock_result.returncode = 0
            mock_result.stdout = "Mocked success"
            mock_result.stderr = ""
            return mock_result

        mock_subprocess_run.side_effect = custom_subprocess_side_effect
        # --- End mock side effects ---

        manager.setup_project()

        # Verify that npm init was called
        mock_subprocess_run.assert_any_call("npm init -y", check=True, capture_output=True, text=True, shell=True, cwd=project_path)

        # Verify that tailwind init was called
        mock_subprocess_run.assert_any_call("npx tailwindcss init -p", cwd=project_path, check=True, capture_output=True, text=True, shell=True)

        # Check that files created by the mocked subprocess exist
        assert (project_path / "vite.config.js").is_file()
        assert (project_path / "tailwind.config.js").is_file()

        # Check that tailwind config was modified
        tailwind_content = (project_path / "tailwind.config.js").read_text()
        assert 'content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"]' in tailwind_content

        # Check that package.json was modified
        pkg_json_path = project_path / "package.json"
        assert pkg_json_path.is_file()
        with open(pkg_json_path, 'r') as f:
            pkg_data = json.load(f)
            assert pkg_data["scripts"]["dev"] == "vite"

        # Verify create_base_files was called
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


    def test_scan_artifacts_identifies_deps_and_creates_paginated_manifest(self, temp_project_dir, mock_subprocess_run):
        project_path = temp_project_dir
        # The manager now calculates path relative to 'src', so we must create it.
        (project_path / "src").mkdir(exist_ok=True)
        manager = ArtifactManager(project_path)

        # Create dummy package.json
        with open(project_path / "package.json", "w") as f:
            json.dump({"name": "test-project", "dependencies": {}}, f)

        artifacts_dir = project_path / "claude_artifacts"
        (artifacts_dir / "artifact1.jsx").write_text("import React from 'react'; export default () => <div />;")
        (artifacts_dir / "artifact2.jsx").write_text("import { someUtil } from 'new-dependency'; export default () => <div />;")
        (artifacts_dir / "artifact3.jsx").write_text("import clsx from 'clsx'; export default () => <div />;")

        found_artifacts = manager.scan_artifacts()

        assert len(found_artifacts) == 3

        # Check main manifest
        manifest_path = project_path / "public" / "manifest.json"
        assert manifest_path.is_file()
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
            assert manifest_data["totalArtifacts"] == 3
            assert manifest_data["totalPages"] == 1
            assert manifest_data["artifactsPerPage"] == 20 # Using the constant

        # Check paginated artifact file
        page1_path = project_path / "public" / "artifacts-1.json"
        assert page1_path.is_file()
        with open(page1_path, 'r') as f:
            page_data = json.load(f)
            assert len(page_data) == 3
            assert any(a['id'] == 'artifact1' for a in page_data)
            # Check path correction
            assert any(a['path'] == '../claude_artifacts/artifact1.jsx' for a in page_data)


        # Check if update_dependencies was called correctly for the new dependency
        # The order of dependencies in the command might vary.
        install_call_found = False
        for call_args in mock_subprocess_run.call_args_list:
            command = call_args[0][0]
            if "npm install" in command and "new-dependency@latest" in command and "react@latest" in command:
                install_call_found = True
                break
        assert install_call_found, "npm install for new dependencies was not called correctly."

        # Ensure it did not try to install 'clsx' which is a base dependency
        # This check is a bit more complex because dependencies are batched.
        # We check that 'clsx' is not in any of the install commands.
        clsx_install_found = False
        for call_args in mock_subprocess_run.call_args_list:
            command = call_args[0][0]
            if "npm install" in command and "clsx" in command:
                clsx_install_found = True
                break
        assert not clsx_install_found, "Should not have tried to install 'clsx' again."


    def test_update_dependencies_installs_new_deps_batched(self, temp_project_dir, mock_subprocess_run):
        project_path = temp_project_dir
        manager = ArtifactManager(project_path)

        # Create package.json with some existing dependencies
        initial_deps = {"existing-dep": "1.0.0"}
        with open(manager.package_json, "w") as f:
            json.dump({"name": "test-project", "dependencies": initial_deps}, f)

        required_deps = {"new-dep1", "new-dep2", "existing-dep", "clsx"} # clsx is a base_dependency

        manager.update_dependencies(required_deps)

        # Should install new-dep1 and new-dep2 in a single batched command.
        # The order of deps in the command might vary, so we check for both.
        install_command_found = False
        for call_args in mock_subprocess_run.call_args_list:
            command = call_args[0][0]
            if "npm install" in command:
                install_command_found = True
                assert "new-dep1@latest" in command
                assert "new-dep2@latest" in command
                assert "existing-dep" not in command
                assert "clsx" not in command
                break
        assert install_command_found, "The batched npm install command was not found."
