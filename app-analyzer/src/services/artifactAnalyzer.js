// src/services/artifactAnalyzer.js
import fs from 'fs/promises';
import path from 'path';
import * as acorn from 'acorn';
import * as walk from 'acorn-walk';

const ARTIFACTS_DIR = path.join(process.cwd(), 'src', 'claude_artifacts');
const UI_COMPONENTS_DIR = path.join(process.cwd(), 'src', 'components', 'ui');

// List of known UI components from shadcn/ui
const KNOWN_UI_COMPONENTS = [
  'alert',
  'button',
  'card',
  'dialog',
  'dropdown-menu',
  'input',
  'label',
  'popover',
  'select',
  'separator',
  'tabs',
  'toast',
];

export async function analyzeArtifacts() {
  try {
    // Get list of artifacts
    const artifactFiles = await fs.readdir(ARTIFACTS_DIR);

    // Get list of installed packages from package.json
    const packageJson = JSON.parse(
      await fs.readFile(path.join(process.cwd(), 'package.json'), 'utf-8')
    );
    const installedDependencies = {
      ...packageJson.dependencies,
      ...packageJson.devDependencies
    };

    // Get list of installed UI components
    const installedComponents = await fs.readdir(UI_COMPONENTS_DIR);

    const analysis = {
      newArtifacts: [],
      missingDependencies: [],
      missingComponents: [],
    };

    // Analyze each artifact
    for (const file of artifactFiles) {
      if (!file.endsWith('.jsx') && !file.endsWith('.js')) continue;

      const artifactPath = path.join(ARTIFACTS_DIR, file);
      const artifactContent = await fs.readFile(artifactPath, 'utf-8');

      // Parse the file
      const ast = acorn.parse(artifactContent, {
        sourceType: 'module',
        ecmaVersion: 'latest',
      });

      // Track dependencies and components used
      const dependencies = new Set();
      const uiComponents = new Set();

      // Walk the AST to find imports
      walk.simple(ast, {
        ImportDeclaration(node) {
          const source = node.source.value;

          // Check if it's a package import
          if (!source.startsWith('.') && !source.startsWith('@/')) {
            dependencies.add(source);
          }

          // Check if it's a UI component import
          if (source.includes('@/components/ui/')) {
            const componentName = source.split('/').pop();
            uiComponents.add(componentName);
          }
        }
      });

      // Check for missing dependencies
      for (const dep of dependencies) {
        if (!installedDependencies[dep]) {
          analysis.missingDependencies.push({
            name: dep,
            // You could add version detection logic here
          });
        }
      }

      // Check for missing UI components
      for (const comp of uiComponents) {
        if (!installedComponents.includes(`${comp}.jsx`)) {
          analysis.missingComponents.push({
            name: comp,
          });
        }
      }

      // Add to new artifacts if not previously analyzed
      analysis.newArtifacts.push({
        name: file,
        dependencies: Array.from(dependencies),
        uiComponents: Array.from(uiComponents),
      });
    }

    return analysis;

  } catch (error) {
    console.error('Analysis failed:', error);
    throw error;
  }
}