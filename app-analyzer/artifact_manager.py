import os
import json
import subprocess
from pathlib import Path
import re


class ArtifactManager:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.artifacts_dir = self.root_dir / "claude_artifacts"
        self.ui_dir = self.root_dir / "src" / "components" / "ui"
        self.package_json = self.root_dir / "package.json"

        # Create necessary directories
        self.artifacts_dir.mkdir(exist_ok=True)
        self.ui_dir.mkdir(parents=True, exist_ok=True)

        # Initialize base dependencies
        self.base_dependencies = {
            "@radix-ui/react-icons": "^1.3.0",
            "class-variance-authority": "^0.7.0",
            "clsx": "^2.1.0",
            "lucide-react": "^0.299.0",
            "tailwind-merge": "^2.2.0",
            "tailwindcss-animate": "^1.0.7",
            "@radix-ui/react-slot": "^1.0.2"
        }

    def run_command(self, command, check=True):
        """Run a shell command and handle errors."""
        try:
            # Security fix: Split command and avoid shell=True
            if isinstance(command, str):
                command = command.split()
            
            result = subprocess.run(
                command,
                check=check,
                capture_output=True,
                text=True,
                shell=False,  # Security fix: disable shell execution
                cwd=self.root_dir  # Ensure commands run in correct directory
            )
            if result.stdout:
                print(result.stdout)
            if result.stderr and "npm WARN" not in result.stderr:
                print(result.stderr)
            return result
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e.cmd}")
            print(f"Error output: {e.stderr}")
            if check:
                raise
            return e

    def setup_project(self):
        """Initialize project with necessary configuration and dependencies."""
        # Create or update package.json
        if not self.package_json.exists():
            self.run_command(["npm", "init", "-y"])

        # Install base dependencies
        deps_list = [f"{k}@{v}" for k, v in self.base_dependencies.items()]
        self.run_command(["npm", "install"] + deps_list)

        # Create initial project structure
        self.create_base_files()

        # Install dev dependencies
        self.run_command(["npm", "install", "-D", "tailwindcss", "postcss", "autoprefixer"])
        
        # Initialize tailwind with better error handling
        try:
            self.run_command(["npx", "tailwindcss", "init", "-p"])
        except subprocess.CalledProcessError as e:
            print(f"Warning: Tailwind initialization failed: {e}")
            print("You may need to initialize Tailwind manually later.")

    def create_base_files(self):
        """Create necessary base files for the project."""
        # Create src/lib/utils.js
        utils_dir = self.root_dir / "src" / "lib"
        utils_dir.mkdir(parents=True, exist_ok=True)
        utils_content = """
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
"""
        (utils_dir / "utils.js").write_text(utils_content)

        # Create main App.jsx
        app_content = """
import React, { useState, useEffect } from 'react';
import { Card } from './components/ui/card';

function App() {
  const [artifacts, setArtifacts] = useState([]);
  const [selectedArtifact, setSelectedArtifact] = useState(null);

  useEffect(() => {
    // Load artifacts from claude_artifacts directory
    const loadArtifacts = async () => {
      const response = await fetch('/api/artifacts');
      const data = await response.json();
      setArtifacts(data);
    };
    loadArtifacts();
  }, []);

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Claude Artifacts</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {artifacts.map((artifact) => (
          <Card
            key={artifact.id}
            className="p-4 cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => setSelectedArtifact(artifact)}
          >
            <h2 className="text-xl font-semibold">{artifact.name}</h2>
            <p className="text-gray-600">{artifact.description}</p>
          </Card>
        ))}
      </div>
      {selectedArtifact && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-4 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto">
            <h2 className="text-2xl font-bold mb-4">{selectedArtifact.name}</h2>
            <div id="artifact-container"></div>
            <button
              className="mt-4 px-4 py-2 bg-gray-200 rounded"
              onClick={() => setSelectedArtifact(null)}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
"""
        (self.root_dir / "src" / "App.jsx").write_text(app_content)

    def scan_artifacts(self):
        """Scan claude_artifacts directory and update project configuration."""
        artifacts = []
        required_dependencies = set()

        # Scan for artifacts
        for file_path in self.artifacts_dir.glob("*"):
            if file_path.is_file():
                with open(file_path, 'r') as f:
                    content = f.read()

                    # Extract imports to identify dependencies
                    import_pattern = r'import\s+.*?from\s+[\'"]([^\.][^\'\"]+)[\'"]'
                    imports = re.findall(import_pattern, content)
                    required_dependencies.update(imports)

                    artifacts.append({
                        "id": file_path.stem,
                        "name": file_path.stem.replace("-", " ").title(),
                        "path": str(file_path.relative_to(self.root_dir)),
                        "type": "react" if file_path.suffix in [".jsx", ".tsx"] else "vanilla"
                    })

        # Update package.json with new dependencies
        self.update_dependencies(required_dependencies)

        return artifacts

    def update_dependencies(self, required_deps):
        """Update package.json with new dependencies."""
        try:
            with open(self.package_json, 'r') as f:
                package_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not read package.json: {e}")
            return

        current_deps = package_data.get("dependencies", {})
        new_deps = False

        for dep in required_deps:
            if dep not in current_deps and dep not in self.base_dependencies:
                new_deps = True
                try:
                    # Use latest version by default
                    self.run_command(["npm", "install", f"{dep}@latest"])
                except subprocess.CalledProcessError as e:
                    print(f"Warning: Failed to install {dep}: {e}")
                    continue

        if new_deps:
            print("New dependencies installation completed!")
        else:
            print("No new dependencies needed.")


from flask import Flask, jsonify, send_from_directory, request

# Initialize Flask App
app = Flask(__name__)

# Get the absolute path to the app-analyzer directory
current_dir = os.path.dirname(os.path.abspath(__file__))
app_analyzer_dir = Path(current_dir)

# Initialize the artifact manager
manager = ArtifactManager(app_analyzer_dir)

@app.route('/api/artifacts', methods=['GET'])
def get_artifacts():
    """API endpoint to get the list of artifacts."""
    artifacts = manager.scan_artifacts()
    return jsonify(artifacts)

@app.route('/api/artifact-source')
def artifact_source():
    """API endpoint to get the source code of an artifact."""
    artifact_path = request.args.get('path')
    if not artifact_path:
        return "Missing path parameter", 400

    # Security: Ensure the path is relative and within the artifacts directory
    safe_base_path = manager.artifacts_dir.resolve()
    target_path = (manager.artifacts_dir / artifact_path).resolve()

    if not target_path.is_file() or not target_path.is_relative_to(safe_base_path):
        return "Invalid or unauthorized path", 403

    return send_from_directory(manager.artifacts_dir, artifact_path, as_attachment=False)

@app.route('/<path:path>')
def serve_static(path):
    # This is for serving the main app, not for the API
    return send_from_directory(manager.root_dir, path)

if __name__ == "__main__":
    # Setup the project
    print("Setting up project...")
    manager.setup_project()

    # Scan for artifacts
    print("\nScanning for artifacts...")
    artifacts = manager.scan_artifacts()

    print(f"\nFound {len(artifacts)} artifacts:")
    for artifact in artifacts:
        print(f"- {artifact['name']} ({artifact['type']})")

    # Run the Flask app
    print("\nStarting Flask server...")
    app.run(port=5001, debug=True)