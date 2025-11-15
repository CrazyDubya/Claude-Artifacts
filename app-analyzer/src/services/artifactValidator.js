// app-analyzer/src/services/artifactValidator.js

const XSS_PATTERNS = [
  'innerHTML',
  'outerHTML',
  'document.write',
  'insertAdjacentHTML',
  'dangerouslySetInnerHTML'
];
const DANGEROUS_FUNCTIONS = [
    'eval\\(',
    'new Function\\(',
    'setTimeout\\s*\\(\\s*[\'"`]',
    'setInterval\\s*\\(\\s*[\'"`]',
];
const ALLOWED_PACKAGES = [
    "@radix-ui/react-icons", "class-variance-authority", "clsx",
    "lucide-react", "tailwind-merge", "tailwindcss-animate",
    "@radix-ui/react-slot", "react", "react-dom", "prop-types"
];

const FORBIDDEN_REGEX = new RegExp([...DANGEROUS_FUNCTIONS].join('|'), 'g');
const XSS_REGEX = new RegExp(XSS_PATTERNS.join('|'), 'g');


export class ArtifactValidator {
  /**
   * Validates the artifact's source code against a set of security rules.
   * @param {string} sourceCode - The source code of the artifact.
   * @param {string} filename - The name of the artifact file.
   * @returns {{isValid: boolean, issues: string[]}} - The validation result.
   */
  static validate(sourceCode, filename) {
    if (!sourceCode) {
      return { isValid: false, issues: ['Source code is empty or null.'] };
    }

    const xssIssues = this.checkForXSS(sourceCode, filename);
    const importIssues = this.validateImports(sourceCode, filename);
    const dangerousFunctionIssues = this.checkForDangerousFunctions(sourceCode, filename);

    const issues = [...xssIssues, ...importIssues, ...dangerousFunctionIssues];

    return {
      isValid: issues.length === 0,
      issues,
    };
  }

  static checkForDangerousFunctions(sourceCode, filename) {
    const issues = [];
    const dangerousMatches = sourceCode.match(FORBIDDEN_REGEX);
    if (dangerousMatches) {
        dangerousMatches.forEach(match => {
            issues.push(`Dangerous function call found in ${filename}: ${match.trim()}`);
        });
    }
    return issues;
  }

  /**
   * Checks for potential XSS vulnerabilities in the code.
   * @param {string} sourceCode - The source code to check.
   * @param {string} filename - The name of the file being checked.
   * @returns {string[]} - A list of identified XSS-related issues.
   */
  static checkForXSS(sourceCode, filename) {
    const issues = [];
    const xssMatches = sourceCode.match(XSS_REGEX);
    if (xssMatches) {
      xssMatches.forEach(match => {
        issues.push(`Potential XSS vulnerability found in ${filename}: ${match.trim()}`);
      });
    }
    return issues;
  }

  /**
   * Validates the imports in the code against a list of allowed packages.
   * @param {string} sourceCode - The source code to check.
   * @param {string} filename - The name of the file being checked.
   * @returns {string[]} - A list of identified import-related issues.
   */
  static validateImports(sourceCode, filename) {
    const issues = [];
    const importPattern = /import\s+.*?from\s+['"](.*?)['"]/g;
    let match;
    while ((match = importPattern.exec(sourceCode)) !== null) {
      const importPath = match[1];
      if (importPath.startsWith('./') || importPath.startsWith('../') || importPath.startsWith('@/')) {
        continue;
      }
      const isAllowed = ALLOWED_PACKAGES.some(pkg => importPath.startsWith(pkg));
      if (!isAllowed) {
        issues.push(`Disallowed import found in ${filename}: ${importPath}`);
      }
    }
    return issues;
  }
}