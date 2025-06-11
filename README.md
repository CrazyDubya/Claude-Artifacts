# Claude Artifact Manager

## Purpose

`claude-artifact-manager` is a Python-based CLI tool designed to help developers, particularly those working with AI-generated outputs from models like Claude, to quickly set up and manage a local React-based project for viewing and interacting with these artifacts. Artifacts are typically HTML, JavaScript (especially React components), or other web content. This tool automates the creation of a Vite-powered React project, pre-configured with Tailwind CSS, and provides commands to initialize, scan for, and add new artifacts.

## Features

*   **Project Initialization**: Quickly scaffold a new React project with Vite, Tailwind CSS, and necessary boilerplate.
*   **Artifact Scanning**: Scan a designated directory (`claude_artifacts/`) for new artifact files.
*   **Dependency Management**: (Basic) Identifies simple import statements in artifacts to suggest potential npm dependencies. (Note: This feature is rudimentary and may require manual intervention for complex dependencies or those not available on npm.)
*   **Dynamic Artifact Loading**: The generated React app can dynamically load and display registered artifacts.
*   **Base UI Components**: Includes a set of basic UI components (Card, Button, etc.) from shadcn/ui to get started.
*   **CLI Interface**: Easy-to-use commands for managing your artifact project.
*   **Extensible**: Designed to be a starting point, allowing developers to customize and expand the generated project.

## Installation

The `claude-artifact-manager` is a Python package and can be installed using pip. Ensure you have Python 3.7+ installed.

```bash
# Coming soon: Installation via PyPI
# pip install claude-artifact-manager

# For now, to install from source (after cloning this repository):
pip install .
# Or for development mode:
pip install -e .
```

You will also need Node.js and npm installed to work with the generated React project.

## CLI Usage

The main command is `claude-artifact-manager`.

### `init <project_directory>`

Initializes a new artifact viewing project in the specified directory.

```bash
claude-artifact-manager init my-artifact-viewer
cd my-artifact-viewer
```

This command will:
1.  Create the `my-artifact-viewer` directory.
2.  Set up a `package.json` file.
3.  Install base dependencies (like React, Tailwind CSS, Vite).
4.  Create initial project files:
    *   `index.html` (main entry point for Vite)
    *   `vite.config.js` (Vite configuration)
    *   `tailwind.config.js` (Tailwind CSS configuration)
    *   `postcss.config.js` (PostCSS configuration)
    *   `src/main.jsx` (React entry point)
    *   `src/App.jsx` (Main application component)
    *   `src/index.css` (Base Tailwind styles)
    *   `src/lib/utils.js` (Utility functions for UI components)
    *   `src/components/ui/` (Directory for pre-included UI components like Card, Button)
    *   `claude_artifacts/` (Directory where your HTML/JS artifacts should be placed)
    *   `public/` (Directory for static assets, including the generated `claude_artifacts_manifest.json`)

After initialization, `cd` into your project directory and run `npm run dev` to start the Vite development server.

### `scan [--project <project_directory>]`

Scans the `claude_artifacts/` directory within your project for artifact files. It then updates `public/claude_artifacts_manifest.json`, which the React application uses to list and load artifacts.

```bash
# From within the project directory:
claude-artifact-manager scan

# Or specifying the project directory:
claude-artifact-manager scan --project ./my-artifact-viewer
```

### `add <artifact_file_path> --project <project_directory>`

Copies a given artifact file into the project's `claude_artifacts/` directory and then runs a scan to update the manifest.

```bash
claude-artifact-manager add ../my-generated-component.jsx --project ./my-artifact-viewer
```

## Generated Project Structure

A project initialized with `claude-artifact-manager` will have a structure similar to this:

```
my-artifact-viewer/
├── claude_artifacts/       # Place your HTML/JS artifacts here
│   └── example.jsx
├── public/
│   └── claude_artifacts_manifest.json # Auto-generated list of artifacts
├── src/
│   ├── components/
│   │   └── ui/             # Pre-included shadcn/ui components (Card, Button, etc.)
│   │       ├── button.jsx
│   │       └── card.jsx
│   ├── lib/
│   │   └── utils.js        # Utility for cn (classnames)
│   ├── App.jsx             # Main React application shell
│   ├── index.css           # Tailwind CSS directives
│   └── main.jsx            # React DOM entry point
├── index.html              # Vite entry HTML file
├── package.json            # NPM dependencies and scripts
├── tailwind.config.js      # Tailwind CSS configuration
├── vite.config.js          # Vite configuration
└── postcss.config.js       # PostCSS configuration (for Tailwind)
```

## Working with Artifacts

1.  **Place Artifacts**: Copy your generated HTML files or React components (`.jsx`, `.tsx`) into the `claude_artifacts/` directory of your initialized project.
2.  **Run Scan**: After adding new artifacts, run `claude-artifact-manager scan` from your project's root directory. This updates the manifest.
3.  **Develop**: Start the Vite dev server using `npm run dev`. Open your browser to the local address provided (usually `http://localhost:5173`).
4.  **View Artifacts**: The main page of the application will list available artifacts. Clicking on an artifact name will attempt to render it in a modal dialog.

## Displaying Artifacts

The `App.jsx` component dynamically imports artifacts listed in `public/claude_artifacts_manifest.json`.
*   React components (`.jsx`, `.tsx`) are expected to have a default export.
*   HTML files can also be added. The current `App.jsx` template is primarily set up for React components. Displaying raw HTML might require adjustments to the template (e.g., using an `iframe` or `dangerouslySetInnerHTML` for HTML content, which is not implemented by default).

The path in `claude_artifacts_manifest.json` for each artifact is relative to the `src` directory for dynamic imports. For example, an artifact at `claude_artifacts/MyComponent.jsx` will have a path like `../claude_artifacts/MyComponent.jsx` in the manifest, suitable for `import(\`../claude_artifacts/MyComponent.jsx\`)` from `src/App.jsx`.

**Important for JavaScript/React Artifacts**:
*   Ensure your artifact components are self-contained or use dependencies available in the generated React project.
*   Complex dependencies might need to be manually added to the `package.json` of the generated project (`npm install some-dependency`).
*   The dynamic import path relies on Vite's behavior. Artifacts are typically placed in `claude_artifacts` which is outside `src`, so paths are like `../claude_artifacts/yourfile.jsx`.

## Scaling for Many Artifacts

The default setup loads the entire list of artifacts from `claude_artifacts_manifest.json` to display them as clickable cards. This is fine for a moderate number of artifacts.

If you have hundreds or thousands of artifacts:
1.  **Pagination/Virtualization for Display**: The card list in `App.jsx` would need to be updated to use pagination or a virtualized list (e.g., using `react-window` or `react-virtualized`) to avoid rendering too many DOM elements at once.
2.  **Backend Search/Filtering**: Instead of fetching the entire manifest, you might implement a simple backend (or a more complex one if needed) that the `claude-artifact-manager scan` command populates. The frontend would then query this backend to search or page through artifacts. `claude-artifact-manager` itself does not provide this backend.
3.  **Static Site Generation (SSG)**: For very large, relatively static sets of artifacts, consider using Vite's SSG capabilities or a framework like Next.js or Astro to pre-render pages for each artifact or groups of artifacts. This would be an advanced customization.
4.  **Manifest Sharding**: If the manifest JSON itself becomes too large, you could modify the `scan` command to create multiple smaller manifest files (e.g., one per category or by date) and adjust the frontend to load them as needed.

The current tool provides a solid foundation. For massive scale, these strategies would be implemented by modifying the generated React project's code.

## Customization

The generated project is a standard Vite + React + Tailwind CSS project. You are free to:
*   Modify `App.jsx` to change how artifacts are displayed or loaded.
*   Add new React components or routes.
*   Install additional npm packages.
*   Customize Tailwind CSS theme in `tailwind.config.js`.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
