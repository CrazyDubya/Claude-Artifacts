# tests/integration/test_cli.py
import pytest
import json
import subprocess # Required for specifying MagicMock for subprocess.CompletedProcess
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import MagicMock # For more complex side_effect configurations if needed

from claude_artifact_manager.cli import main as cli_main
# from claude_artifact_manager.manager import ArtifactManager # Only if directly interacting

class TestCliIntegration:

    def test_init_command_creates_project_successfully(self, temp_project_dir, mock_subprocess_run):
        runner = CliRunner()
        project_name = "my_test_project"
        project_path = temp_project_dir / project_name

        # Simulate file creation by mocked subprocess calls for init
        def custom_subprocess_side_effect_init(*args, **kwargs):
            command_str = args[0]
            cwd = Path(kwargs.get("cwd", project_path))

            if command_str == "npm init -y":
                pkg_json_path = cwd / "package.json"
                pkg_json_path.write_text(json.dumps({"name": project_name, "version": "0.1.0", "scripts": {}}))
            elif command_str == "npx tailwindcss init -p":
                (cwd / "tailwind.config.js").write_text("module.exports = { content: [], theme: {}, plugins: [] };")
                (cwd / "postcss.config.js").write_text("module.exports = { plugins: { tailwindcss: {}, autoprefixer: {} } };")

            mock_result = MagicMock(spec=subprocess.CompletedProcess)
            mock_result.returncode = 0
            mock_result.stdout = "Mocked subprocess success"
            mock_result.stderr = ""
            return mock_result

        mock_subprocess_run.side_effect = custom_subprocess_side_effect_init

        result = runner.invoke(cli_main, ["init", str(project_path)])

        assert result.exit_code == 0, f"CLI Error: {result.output}"
        assert f"Initializing project in {project_path}" in result.output
        assert f"Project initialized successfully in {project_path}" in result.output

        assert project_path.is_dir()
        assert (project_path / "package.json").is_file()
        assert (project_path / "vite.config.js").is_file()
        assert (project_path / "src" / "App.jsx").is_file()
        assert (project_path / "claude_artifacts").is_dir()
        assert (project_path / "public").is_dir()
        assert (project_path / "src" / "components" / "ui").is_dir()


    def test_add_command_copies_artifact_and_updates_manifest(self, temp_project_dir, mock_subprocess_run):
        runner = CliRunner()
        project_name = "add_test_proj"
        project_path = temp_project_dir / project_name

        # --- Mock side effects for init phase ---
        def custom_subprocess_side_effect_add_init(*args, **kwargs):
            command_str = args[0]
            cwd = Path(kwargs.get("cwd", project_path))
            if command_str == "npm init -y":
                (cwd / "package.json").write_text(json.dumps({"name": project_name, "version": "0.1.0", "scripts": {}}))
            elif command_str == "npx tailwindcss init -p":
                (cwd / "tailwind.config.js").write_text("module.exports = { content: [], theme: {}, plugins: [] };")
                (cwd / "postcss.config.js").write_text("module.exports = { plugins: { tailwindcss: {}, autoprefixer: {} } };")

            # Default for other commands (like npm install new-dep)
            mock_result = MagicMock(spec=subprocess.CompletedProcess)
            mock_result.returncode = 0
            mock_result.stdout = "Mocked subprocess success"
            mock_result.stderr = ""
            return mock_result
        mock_subprocess_run.side_effect = custom_subprocess_side_effect_add_init
        # --- End mock side effects for init phase ---

        init_result = runner.invoke(cli_main, ["init", str(project_path)])
        assert init_result.exit_code == 0, f"Init failed: {init_result.output}"

        # Ensure package.json exists after init for the 'add' command's scan part
        if not (project_path / "package.json").exists():
             (project_path / "package.json").write_text(json.dumps({"name": project_name, "version": "0.1.0", "scripts": {}, "dependencies":{}}))


        dummy_artifact_content = "import React from 'react'; import Something from 'new-dep-for-add'; export default () => <div>Dummy</div>;"
        artifact_file = temp_project_dir / "dummy_artifact.jsx"
        artifact_file.write_text(dummy_artifact_content)

        add_result = runner.invoke(cli_main, ["add", str(artifact_file), "--project", str(project_path)])

        assert add_result.exit_code == 0, f"Add command failed: {add_result.output}"
        assert f"Adding artifact '{artifact_file.name}'" in add_result.output
        assert "Artifact copied to" in add_result.output
        assert "Scanning artifacts to update dependencies..." in add_result.output

        assert (project_path / "claude_artifacts" / artifact_file.name).is_file()

        manifest_path = project_path / "public" / "claude_artifacts_manifest.json"
        assert manifest_path.is_file()
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
        assert len(manifest_data) == 1
        assert manifest_data[0]["id"] == "dummy_artifact"

        # Check that 'new-dep-for-add' was attempted to be installed via the scan triggered by add
        mock_subprocess_run.assert_any_call("npm install new-dep-for-add@latest", check=True, capture_output=True, text=True, shell=True, cwd=project_path)


    def test_scan_command_generates_manifest(self, temp_project_dir, mock_subprocess_run):
        runner = CliRunner()
        project_name = "scan_test_proj"
        project_path = temp_project_dir / project_name

        # --- Mock side effects for init phase of scan test ---
        def custom_subprocess_side_effect_scan_init(*args, **kwargs):
            command_str = args[0]
            cwd = Path(kwargs.get("cwd", project_path))
            if command_str == "npm init -y":
                (cwd / "package.json").write_text(json.dumps({"name": project_name, "version": "0.1.0", "scripts": {}}))
            elif command_str == "npx tailwindcss init -p":
                (cwd / "tailwind.config.js").write_text("module.exports = { content: [], theme: {}, plugins: [] };")
                (cwd / "postcss.config.js").write_text("module.exports = { plugins: { tailwindcss: {}, autoprefixer: {} } };")

            # Default for other commands (like npm install some-dep)
            mock_result = MagicMock(spec=subprocess.CompletedProcess)
            mock_result.returncode = 0
            mock_result.stdout = "Mocked subprocess success"
            mock_result.stderr = ""
            return mock_result
        mock_subprocess_run.side_effect = custom_subprocess_side_effect_scan_init
        # --- End mock side effects for init phase ---

        init_result = runner.invoke(cli_main, ["init", str(project_path)])
        assert init_result.exit_code == 0, f"Init failed for scan test: {init_result.output}"

        artifacts_dir = project_path / "claude_artifacts"
        (artifacts_dir / "scan_art1.jsx").write_text("export default () => 'art1';")
        (artifacts_dir / "scan_art2.jsx").write_text("import Something from 'some-dep'; export default () => 'art2';")

        # Ensure package.json exists as scan_artifacts -> update_dependencies needs it
        # The init mock should create this, but double check or create a default if needed for the scan part
        if not (project_path / "package.json").exists():
            (project_path / "package.json").write_text(json.dumps({"name": project_name, "version": "0.1.0", "dependencies": {}}))


        scan_result = runner.invoke(cli_main, ["scan", "--project", str(project_path)])

        assert scan_result.exit_code == 0, f"Scan command failed: {scan_result.output}"
        assert "Scanning artifacts in" in scan_result.output
        assert "Found 2 artifacts" in scan_result.output

        manifest_path = project_path / "public" / "claude_artifacts_manifest.json"
        assert manifest_path.is_file()
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
        assert len(manifest_data) == 2
        assert any(a["id"] == "scan_art1" for a in manifest_data)
        assert any(a["id"] == "scan_art2" for a in manifest_data)

        mock_subprocess_run.assert_any_call("npm install some-dep@latest", check=True, capture_output=True, text=True, shell=True, cwd=project_path)


    def test_init_missing_project_dir_fails(self, temp_project_dir): # temp_project_dir not strictly needed here
        runner = CliRunner()
        result = runner.invoke(cli_main, ["init"])
        assert result.exit_code != 0
        assert "Missing argument 'PROJECT_DIRECTORY'" in result.output # Click's default message format

    def test_add_missing_artifact_file_fails(self, temp_project_dir):
        runner = CliRunner()
        project_path = temp_project_dir / "proj"
        project_path.mkdir()

        result = runner.invoke(cli_main, ["add", "non_existent_artifact.jsx", "--project", str(project_path)])
        assert result.exit_code != 0
        assert "Invalid value for 'ARTIFACT_FILE': File 'non_existent_artifact.jsx' does not exist." in result.output

    def test_add_missing_project_option_fails(self, temp_project_dir):
        runner = CliRunner()
        artifact_file = temp_project_dir / "dummy.jsx"
        artifact_file.write_text("content")

        result = runner.invoke(cli_main, ["add", str(artifact_file)])
        assert result.exit_code != 0
        assert "Missing option '--project'" in result.output

