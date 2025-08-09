# tests/integration/test_cli.py
import pytest
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import MagicMock

from claude_artifact_manager.cli import main as cli_main
from claude_artifact_manager.manager import ArtifactManager

@pytest.fixture
def mock_manager_methods(monkeypatch):
    """Mocks methods on the ArtifactManager class."""
    setup_mock = MagicMock()
    scan_mock = MagicMock(return_value=[{"id": "test-artifact"}])

    monkeypatch.setattr(ArtifactManager, "setup_project", setup_mock)
    monkeypatch.setattr(ArtifactManager, "scan_artifacts", scan_mock)

    # Return the mocks so they can be inspected in tests
    return setup_mock, scan_mock

class TestCliCommands:

    def test_init_command(self, temp_project_dir, mock_manager_methods):
        setup_mock, _ = mock_manager_methods
        runner = CliRunner()
        project_path = temp_project_dir / "my-project"

        result = runner.invoke(cli_main, ["init", str(project_path)])

        assert result.exit_code == 0
        assert "Initializing project" in result.output
        setup_mock.assert_called_once()

    def test_scan_command(self, temp_project_dir, mock_manager_methods):
        _, scan_mock = mock_manager_methods
        runner = CliRunner()
        project_path = temp_project_dir / "my-project"
        project_path.mkdir() # The command expects the project dir to exist

        result = runner.invoke(cli_main, ["scan", "--project", str(project_path)])

        assert result.exit_code == 0
        assert "Scan complete" in result.output
        scan_mock.assert_called_once()

    def test_add_command(self, temp_project_dir, mock_manager_methods):
        _, scan_mock = mock_manager_methods
        runner = CliRunner()
        project_path = temp_project_dir / "my-project"
        project_path.mkdir()

        artifact_file = temp_project_dir / "artifact.jsx"
        artifact_file.write_text("dummy content")

        result = runner.invoke(cli_main, ["add", str(artifact_file), "--project", str(project_path)])

        assert result.exit_code == 0, f"Error: {result.output}"
        assert "Adding artifact" in result.output
        assert "Artifact copied" in result.output

        # A real ArtifactManager is created, so its __init__ runs and creates this dir
        assert (project_path / "claude_artifacts" / "artifact.jsx").exists()

        scan_mock.assert_called_once()

    def test_init_missing_project_dir_fails(self):
        runner = CliRunner()
        result = runner.invoke(cli_main, ["init"])
        assert result.exit_code != 0
        assert "Missing argument 'PROJECT_DIRECTORY'" in result.output

    def test_add_missing_artifact_file_fails(self, temp_project_dir):
        runner = CliRunner()
        project_path = temp_project_dir / "proj"
        project_path.mkdir()

        result = runner.invoke(cli_main, ["add", "non_existent_artifact.jsx", "--project", str(project_path)])
        assert result.exit_code != 0
        assert "Invalid value for 'ARTIFACT_FILE'" in result.output
        assert "does not exist" in result.output

    def test_add_missing_project_option_fails(self, temp_project_dir):
        runner = CliRunner()
        artifact_file = temp_project_dir / "dummy.jsx"
        artifact_file.write_text("content")

        result = runner.invoke(cli_main, ["add", str(artifact_file)])
        assert result.exit_code != 0
        assert "Missing option '--project'" in result.output
