# Contributing to Claude Artifact Manager

We welcome contributions to the Claude Artifact Manager! Please follow these guidelines.

## Development Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd claude-artifact-manager
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3.  **Install the package in editable mode with test dependencies:**
    ```bash
    pip install -e .[test]
    ```

## Running Tests

This project uses `pytest` for testing.

1.  **Run all tests:**
    To run the complete test suite, execute the following command from the root of the repository:
    ```bash
    pytest
    ```
    Or, using the Python module invocation:
    ```bash
    python -m pytest
    ```
    This command will also automatically generate code coverage reports due to the configuration in `pytest.ini`.

2.  **Test Coverage:**
    *   **Terminal Report:** After the tests complete, a summary of code coverage will be printed to the terminal.
    *   **HTML Report:** For a more detailed, line-by-line coverage report, open the `htmlcov/index.html` file in your web browser. This file is generated in the project root after running tests.
    *   We aim for a high level of test coverage. Please ensure your contributions are well-tested.

3.  **Running Specific Tests:**
    You can run specific test files, classes, or functions using pytest's standard selectors. For example:
    *   Run all tests in a file: `pytest tests/unit/test_manager.py`
    *   Run all tests in a class: `pytest tests/unit/test_manager.py::TestArtifactManager`
    *   Run a specific test method: `pytest tests/unit/test_manager.py::TestArtifactManager::test_initialization_creates_directories`

## Test Structure

*   Tests are located in the `tests/` directory.
*   **Unit tests** for individual modules are in `tests/unit/`.
*   **Integration tests** for CLI commands and component interactions are in `tests/integration/`.
*   Shared test fixtures are defined in `tests/conftest.py`. Key fixtures include:
    *   `temp_project_dir`: Provides an isolated temporary directory for tests that interact with the file system.
    *   `mock_subprocess_run`: Mocks `subprocess.run` to control external command execution (like `npm`) during tests.

## Coding Style
(To be added - e.g., mention linters like Flake8/Ruff, Black for formatting if they are set up later)

## Submitting Changes
(To be added - e.g., fork, branch, PR process)
