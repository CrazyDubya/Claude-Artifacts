import os
import json
import subprocess
from pathlib import Path
import re
import importlib.resources
import sys
import math

# Constants
ARTIFACTS_PER_PAGE = 20

class ArtifactManager:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.artifacts_dir = self.root_dir / "claude_artifacts"
        self.ui_dir = self.root_dir / "src" / "components" / "ui" # For user's project structure
        self.public_dir = self.root_dir / "public"
        self.package_json = self.root_dir / "package.json"

        # Create necessary directories
        # self.ui_dir will create the root project directory because parents=True
        self.ui_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(exist_ok=True)
        self.public_dir.mkdir(exist_ok=True)

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

    def run_command(self, command, check=True, cwd=None, quiet=False):
        """Run a shell command and handle errors."""
        try:
            result = subprocess.run(
                command,
                check=check,
                capture_output=True,
                text=True,
                shell=True,
                cwd=cwd
            )
            if not quiet:
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
            self.run_command("npm init -y", cwd=self.root_dir)

        # Update package.json with scripts
        if self.package_json.exists():
            try:
                package_data = json.loads(self.package_json.read_text())
                package_data["scripts"] = {
                    "dev": "vite",
                    "build": "vite build",
                    "preview": "vite preview",
                    # "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0" # Optional
                }
                # Ensure main field points to something Vite/React friendly if it's not already set
                # For library mode, this would be different. For app mode, index.html is the entry.
                # package_data.pop("main", None) # Or set to appropriate value if building a library
                self.package_json.write_text(json.dumps(package_data, indent=2))
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {self.package_json}. Scripts not added.", file=sys.stderr)
        else:
            print(f"Warning: {self.package_json} not found. Scripts not added.", file=sys.stderr)


        # Install base dependencies
        deps_str = " ".join(f"{k}@{v}" for k, v in self.base_dependencies.items())
        print("Installing base dependencies...")
        self.run_command(f"npm install {deps_str}", cwd=self.root_dir, quiet=True)
        print("Base dependencies installed.")

        # Create initial project structure
        self.create_base_files()

        # Install dev dependencies
        print("Installing dev dependencies...")
        self.run_command("npm install -D tailwindcss postcss autoprefixer", cwd=self.root_dir, quiet=True)
        self.run_command("npx tailwindcss init -p", cwd=self.root_dir, quiet=True)
        self.run_command("npm install -D vite @vitejs/plugin-react", cwd=self.root_dir, quiet=True)
        print("Dev dependencies installed.")

        # Update tailwind.config.js for JSX content scanning
        tailwind_config_path = self.root_dir / "tailwind.config.js"
        if tailwind_config_path.exists():
            # This is a simplified way; a more robust way would be to parse the JS AST
            # or use a regex, but that's much more complex.
            # For now, assume a simple structure of tailwind.config.js
            config_content = tailwind_config_path.read_text()
            # Replace content: [] with the new content line
            new_content_line = '  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],'
            config_content = re.sub(r'content:\s*\[\s*\]', new_content_line, config_content, count=1)
            # If content was not empty, try a more generic replacement (less safe)
            if 'content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"]' not in config_content:
                 config_content = re.sub(r'content:\s*\[.*?\]', new_content_line, config_content, count=1)
            tailwind_config_path.write_text(config_content)
        else:
            print(f"Warning: {tailwind_config_path} not found. Could not update content scanning paths.", file=sys.stderr)

        # Create vite.config.js
        vite_config_content = """
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
})
"""
        (self.root_dir / "vite.config.js").write_text(vite_config_content)

    def create_base_files(self):
        """Create necessary base files for the project."""
        utils_dir = self.root_dir / "src" / "lib"
        app_jsx_dir = self.root_dir / "src"

        utils_dir.mkdir(parents=True, exist_ok=True)
        app_jsx_dir.mkdir(parents=True, exist_ok=True) # Ensures src directory exists

        try:
            utils_content = importlib.resources.read_text("claude_artifact_manager.templates", "utils.js.template")
            app_content = importlib.resources.read_text("claude_artifact_manager.templates", "App.jsx.template")
        except ModuleNotFoundError:
            print("Error: Template resources package 'claude_artifact_manager.templates' not found.", file=sys.stderr)
            raise
        except FileNotFoundError:
            print("Error: Template files (utils.js.template or App.jsx.template) not found in claude_artifact_manager.templates.", file=sys.stderr)
            raise

        (utils_dir / "utils.js").write_text(utils_content)
        (app_jsx_dir / "App.jsx").write_text(app_content)

        try:
            index_html_content = importlib.resources.read_text("claude_artifact_manager.templates", "index.html.template")
            (self.root_dir / "index.html").write_text(index_html_content)

            main_jsx_content = importlib.resources.read_text("claude_artifact_manager.templates", "main.jsx.template")
            (app_jsx_dir / "main.jsx").write_text(main_jsx_content) # app_jsx_dir is self.root_dir / "src"

            index_css_content = importlib.resources.read_text("claude_artifact_manager.templates", "index.css.template")
            (app_jsx_dir / "index.css").write_text(index_css_content) # app_jsx_dir is self.root_dir / "src"
        except ModuleNotFoundError:
            print("Error: Template resources package 'claude_artifact_manager.templates' not found for html/main.jsx/css.", file=sys.stderr)
            raise
        except FileNotFoundError:
            print("Error: Template file (index.html, main.jsx, or index.css) not found in claude_artifact_manager.templates.", file=sys.stderr)
            raise

        # Copy UI components
        target_ui_dir = self.root_dir / "src" / "components" / "ui"
        target_ui_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Path to the templates within the package
            source_ui_templates_path = importlib.resources.files("claude_artifact_manager") / "templates" / "components" / "ui"

            if source_ui_templates_path.is_dir():
                for item in source_ui_templates_path.iterdir():
                    if item.is_file() and (item.name.endswith(".jsx") or item.name.endswith(".js")):
                        try:
                            file_content = item.read_text(encoding="utf-8")
                            (target_ui_dir / item.name).write_text(file_content, encoding="utf-8")
                        except UnicodeDecodeError:
                            try:
                                file_content_binary = item.read_bytes()
                                (target_ui_dir / item.name).write_bytes(file_content_binary)
                            except Exception as bin_e:
                                print(f"Error copying binary file {item.name}: {bin_e}", file=sys.stderr)
                        except Exception as e:
                            print(f"Error copying UI component {item.name}: {e}", file=sys.stderr)
            else:
                 print(f"Warning: Template UI directory not found at {source_ui_templates_path}. UI components might not be copied.", file=sys.stderr)

        except Exception as e:
            print(f"Error accessing or copying UI component templates: {e}", file=sys.stderr)
            # Non-fatal, as per previous logic

    def scan_artifacts(self):
        """Scan claude_artifacts directory, update dependencies, and create paginated manifest."""
        artifacts = []
        required_dependencies = set()

        # Scan for artifacts
        print(f"Scanning for artifacts in {self.artifacts_dir}...")
        for file_path in sorted(self.artifacts_dir.glob("*")): # Sort for consistent ordering
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                        # Extract imports to identify dependencies
                        import_pattern = r'import\s+.*?from\s+[\'"]([^\.][^\'\"]+)[\'"]'
                        imports = re.findall(import_pattern, content)
                        required_dependencies.update(imports)

                        # The path for dynamic import in React needs to be relative to the component importing it (e.g., App.jsx in src)
                        src_dir = self.root_dir / 'src'
                        relative_path = os.path.relpath(file_path, src_dir)

                        artifacts.append({
                            "id": file_path.stem,
                            "name": file_path.stem.replace("-", " ").title(),
                            "path": relative_path.replace(os.sep, '/'), # Ensure forward slashes for web paths
                            "type": "react" if file_path.suffix in [".jsx", ".tsx"] else "vanilla"
                        })
                except Exception as e:
                    print(f"Could not process file {file_path}: {e}", file=sys.stderr)

        print(f"Found {len(artifacts)} artifacts.")

        # Update package.json with new dependencies
        if required_dependencies:
            self.update_dependencies(required_dependencies)

        # Create paginated artifacts manifest
        total_artifacts = len(artifacts)
        total_pages = math.ceil(total_artifacts / ARTIFACTS_PER_PAGE)

        # Save main manifest file
        manifest_path = self.public_dir / "manifest.json"
        try:
            with open(manifest_path, 'w') as f:
                json.dump({
                    "totalArtifacts": total_artifacts,
                    "totalPages": total_pages,
                    "artifactsPerPage": ARTIFACTS_PER_PAGE
                }, f, indent=2)
            print(f"Main manifest saved to {manifest_path}")
        except IOError as e:
            print(f"Error saving main manifest: {e}", file=sys.stderr)
            return [] # Return empty list on failure

        # Save paginated artifact files
        for i in range(total_pages):
            start_index = i * ARTIFACTS_PER_PAGE
            end_index = start_index + ARTIFACTS_PER_PAGE
            page_artifacts = artifacts[start_index:end_index]

            page_manifest_path = self.public_dir / f"artifacts-{i + 1}.json"
            try:
                with open(page_manifest_path, 'w') as f:
                    json.dump(page_artifacts, f, indent=2)
            except IOError as e:
                print(f"Error saving artifact page {i + 1}: {e}", file=sys.stderr)

        print(f"Saved {total_pages} pages of artifacts.")
        return artifacts

    def update_dependencies(self, required_deps):
        """Update package.json with new dependencies."""
        try:
            with open(self.package_json, 'r') as f:
                package_data = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error reading {self.package_json}: {e}", file=sys.stderr)
            return

        current_deps = package_data.get("dependencies", {})
        new_deps_to_install = []

        for dep in required_deps:
            if dep not in current_deps and dep not in self.base_dependencies:
                new_deps_to_install.append(dep)

        if new_deps_to_install:
            deps_str = " ".join(f"{dep}@latest" for dep in new_deps_to_install)
            print(f"Installing new dependencies: {', '.join(new_deps_to_install)}...")
            self.run_command(f"npm install {deps_str}", cwd=self.root_dir, quiet=True)
            print("New dependencies installed successfully!")