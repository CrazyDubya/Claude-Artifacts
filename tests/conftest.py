# tests/conftest.py
import pytest
import tempfile
from pathlib import Path
import shutil
from unittest.mock import MagicMock, patch

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for a test project and clean it up afterwards."""
    temp_dir = Path(tempfile.mkdtemp(prefix="claude_am_test_"))
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_subprocess_run(monkeypatch):
    """Mocks subprocess.run and allows inspection of calls and control of return values."""
    mock_run = MagicMock(name="subprocess.run")

    # Configure the default return_value of the mock_run itself
    # to be a MagicMock that simulates a CompletedProcess object.
    default_completed_process = MagicMock(
        returncode=0,
        stdout="Mocked subprocess output",
        stderr=""
    )
    # Ensure that if check_returncode() is called on this mock, it doesn't raise an error by default.
    default_completed_process.check_returncode = MagicMock()

    mock_run.return_value = default_completed_process

    # The most common way manager.py imports subprocess is 'import subprocess'.
    # So, we patch 'subprocess.run' where it's defined, or more robustly,
    # where it's used if the import is module-specific.
    # For now, let's assume 'claude_artifact_manager.manager.subprocess.run'
    # is the target if 'import subprocess' is used in manager.py.
    # If 'from subprocess import run' is used, it would be 'claude_artifact_manager.manager.run'.
    # We will try patching 'claude_artifact_manager.manager.subprocess.run' first.
    # If that fails in tests, it means the import in manager.py is different.

    # Using a try-except to attempt patching common import styles for subprocess.run
    # This makes the fixture more resilient to how subprocess is imported in the code under test.
    try:
        # This target assumes 'import subprocess' in manager.py
        monkeypatch.setattr("claude_artifact_manager.manager.subprocess.run", mock_run)
    except AttributeError:
        try:
            # This target assumes 'from subprocess import run' in manager.py
            monkeypatch.setattr("claude_artifact_manager.manager.run", mock_run)
        except AttributeError:
            # Fallback to global patching if specific targets fail, though less ideal.
            # This could happen if subprocess is imported in a very unusual way or if the path is wrong.
            # Consider raising an error or warning here if this fallback is reached,
            # as it might indicate the test setup isn't perfectly aligned with the code.
            print("Warning: Could not find subprocess.run at common locations. Patching globally. Ensure manager.py imports subprocess correctly.")
            monkeypatch.setattr("subprocess.run", mock_run)

    return mock_run
