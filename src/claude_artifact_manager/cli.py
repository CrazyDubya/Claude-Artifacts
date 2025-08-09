import click
from pathlib import Path
import shutil # For the 'add' command
from .manager import ArtifactManager

@click.group()
def main():
    """A CLI tool to manage Claude artifact projects."""
    pass

@main.command()
@click.argument("project_directory", type=click.Path(file_okay=False, dir_okay=True, writable=True, resolve_path=True))
def init(project_directory):
    """Initializes a new Claude artifact project in PROJECT_DIRECTORY."""
    project_path = Path(project_directory)
    click.echo(f"Initializing project in {project_path}...")
    try:
        manager = ArtifactManager(project_path)
        manager.setup_project()
        click.echo(f"Project initialized successfully in {project_path}")
        click.echo(f"Base files created: src/lib/utils.js, src/App.jsx, package.json")
        click.echo("Remember to install Node.js and npm if you haven't already.")
    except Exception as e:
        click.echo(f"Error during project initialization: {e}", err=True)

@main.command()
@click.option("--project", "project_directory", default=".", type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, resolve_path=True), help="The project directory.", show_default=True)
def scan(project_directory):
    """Scans the project's claude_artifacts directory and updates the manifest."""
    project_path = Path(project_directory)
    try:
        manager = ArtifactManager(project_path)
        manager.scan_artifacts()
        click.echo("Scan complete. Manifest and artifact pages have been updated.")
    except Exception as e:
        click.echo(f"Error during scan: {e}", err=True)

@main.command()
@click.argument("artifact_file", type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True))
@click.option("--project", "project_directory", required=True, type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True, resolve_path=True), help="The project directory to add the artifact to.")
def add(artifact_file, project_directory):
    """Adds an artifact file to the project and re-scans the directory."""
    artifact_path = Path(artifact_file)
    project_path = Path(project_directory)

    try:
        manager = ArtifactManager(project_path)
        target_artifacts_dir = manager.artifacts_dir
        target_artifacts_dir.mkdir(parents=True, exist_ok=True)

        destination_path = target_artifacts_dir / artifact_path.name

        click.echo(f"Adding artifact '{artifact_path.name}' to project {project_path}...")
        shutil.copy(artifact_path, destination_path)
        click.echo(f"Artifact copied to {destination_path}")

        click.echo("Re-scanning artifacts directory...")
        manager.scan_artifacts()
        click.echo("Scan complete. Manifest and artifact pages have been updated.")

    except Exception as e:
        click.echo(f"Error adding artifact: {e}", err=True)

if __name__ == '__main__':
    main()
