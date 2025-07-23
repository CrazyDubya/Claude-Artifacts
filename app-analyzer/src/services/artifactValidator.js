// src/services/artifactValidator.js
/**
 * Artifact Security Validator
 * Validates artifacts against security policies before execution
 */

const ALLOWED_PACKAGES = [
  '@radix-ui',
  'lucide-react',
  'react-icons',
  'clsx',
  'tailwind-merge',
  'class-variance-authority',
  'date-fns',
  'lodash',
  'uuid',
  'react',
  'react-dom'
];

const FORBIDDEN_PATTERNS = [
  // Dangerous functions
  /\beval\s*\(/,
  /\bFunction\s*\(/,
  /setTimeout\s*\(\s*['"`]/,
  /setInterval\s*\(\s*['"`]/,
  
  // DOM manipulation
  /\.innerHTML\s*=/,
  /\.outerHTML\s*=/,
  /document\.write\s*\(/,
  /insertAdjacentHTML\s*\(/,
  
  // Network requests to external domains
  /fetch\s*\(\s*['"`]https?:\/\//,
  /XMLHttpRequest/,
  
  // Dynamic imports of external URLs
  /import\s*\(\s*['"`]https?:\/\//,
  
  // File system access
  /require\s*\(\s*['"`]fs['"`]/,
  /import.*from\s*['"`]fs['"`]/
];

const REQUIRED_PATTERNS = [
  // Must be a React component
  /export\s+default\s+/,
  // Must import React
  /import\s+.*React.*from\s*['"`]react['"`]/
];

export class ArtifactValidator {
  /**
   * Validate artifact code for security and compliance
   * @param {string} code - The artifact code to validate
   * @param {string} filename - The filename for context
   * @returns {Object} Validation result
   */
  static validate(code, filename = 'unknown') {
    const result = {
      isValid: true,
      errors: [],
      warnings: [],
      securityIssues: []
    };

    try {
      // Check for forbidden patterns
      for (const pattern of FORBIDDEN_PATTERNS) {
        if (pattern.test(code)) {
          result.securityIssues.push({
            type: 'forbidden_pattern',
            pattern: pattern.source,
            message: `Forbidden pattern detected: ${pattern.source}`
          });
          result.isValid = false;
        }
      }

      // Check for required patterns
      for (const pattern of REQUIRED_PATTERNS) {
        if (!pattern.test(code)) {
          result.errors.push({
            type: 'missing_required',
            pattern: pattern.source,
            message: `Required pattern missing: ${pattern.source}`
          });
          result.isValid = false;
        }
      }

      // Validate imports
      const importValidation = this.validateImports(code);
      if (!importValidation.isValid) {
        result.errors.push(...importValidation.errors);
        result.securityIssues.push(...importValidation.securityIssues);
        result.isValid = false;
      }

      // Check for potential XSS vulnerabilities
      const xssCheck = this.checkForXSS(code);
      if (xssCheck.hasIssues) {
        result.warnings.push(...xssCheck.warnings);
        result.securityIssues.push(...xssCheck.securityIssues);
      }

      // Validate component structure
      const structureValidation = this.validateComponentStructure(code);
      if (!structureValidation.isValid) {
        result.warnings.push(...structureValidation.warnings);
      }

    } catch (error) {
      result.errors.push({
        type: 'validation_error',
        message: `Validation failed: ${error.message}`
      });
      result.isValid = false;
    }

    return result;
  }

  /**
   * Validate imports against allowed packages
   * @param {string} code - The code to check
   * @returns {Object} Import validation result
   */
  static validateImports(code) {
    const result = {
      isValid: true,
      errors: [],
      securityIssues: []
    };

    const importRegex = /import\s+.*?from\s+['"`]([^'"`]+)['"`]/g;
    let match;

    while ((match = importRegex.exec(code)) !== null) {
      const importPath = match[1];
      
      // Skip relative imports
      if (importPath.startsWith('./') || importPath.startsWith('../') || importPath.startsWith('@/')) {
        continue;
      }

      // Check if it's an allowed package
      const isAllowed = ALLOWED_PACKAGES.some(allowed => 
        importPath === allowed || importPath.startsWith(allowed + '/')
      );

      if (!isAllowed) {
        result.securityIssues.push({
          type: 'unauthorized_import',
          importPath,
          message: `Unauthorized import: ${importPath}. Only approved packages are allowed.`
        });
        result.isValid = false;
      }

      // Check for external URL imports
      if (importPath.match(/^https?:\/\//)) {
        result.securityIssues.push({
          type: 'external_url_import',
          importPath,
          message: `External URL import detected: ${importPath}. This is not allowed for security reasons.`
        });
        result.isValid = false;
      }
    }

    return result;
  }

  /**
   * Check for potential XSS vulnerabilities
   * @param {string} code - The code to check
   * @returns {Object} XSS check result
   */
  static checkForXSS(code) {
    const result = {
      hasIssues: false,
      warnings: [],
      securityIssues: []
    };

    // Check for dangerouslySetInnerHTML usage
    if (code.includes('dangerouslySetInnerHTML')) {
      result.hasIssues = true;
      result.securityIssues.push({
        type: 'dangerous_html',
        message: 'Usage of dangerouslySetInnerHTML detected. Ensure content is properly sanitized.'
      });
    }

    // Check for direct user input rendering without sanitization
    const userInputPatterns = [
      /\{[^}]*\.value[^}]*\}/,  // Direct form value rendering
      /\{[^}]*prompt\s*\([^}]*\)/,  // Prompt usage
      /\{[^}]*window\.[^}]*\}/  // Window object usage
    ];

    for (const pattern of userInputPatterns) {
      if (pattern.test(code)) {
        result.hasIssues = true;
        result.warnings.push({
          type: 'potential_xss',
          pattern: pattern.source,
          message: `Potential XSS vulnerability: ${pattern.source}. Ensure user input is sanitized.`
        });
      }
    }

    return result;
  }

  /**
   * Validate React component structure
   * @param {string} code - The code to check
   * @returns {Object} Structure validation result
   */
  static validateComponentStructure(code) {
    const result = {
      isValid: true,
      warnings: []
    };

    // Check if component has proper error handling
    if (!code.includes('try') && !code.includes('catch')) {
      result.warnings.push({
        type: 'missing_error_handling',
        message: 'Consider adding error handling to your component for better reliability.'
      });
    }

    // Check for state management best practices
    if (code.includes('useState') && !code.includes('useCallback') && code.includes('onClick')) {
      result.warnings.push({
        type: 'performance_warning',
        message: 'Consider using useCallback for event handlers to optimize performance.'
      });
    }

    // Check for accessibility considerations
    if (code.includes('<button') && !code.includes('aria-')) {
      result.warnings.push({
        type: 'accessibility_warning',
        message: 'Consider adding ARIA attributes for better accessibility.'
      });
    }

    return result;
  }

  /**
   * Get a summary of validation results
   * @param {Object} validationResult - The validation result
   * @returns {string} Human-readable summary
   */
  static getSummary(validationResult) {
    const { isValid, errors, warnings, securityIssues } = validationResult;
    
    let summary = isValid ? '✅ Validation passed' : '❌ Validation failed';
    
    if (securityIssues.length > 0) {
      summary += `\n🔒 Security issues: ${securityIssues.length}`;
    }
    
    if (errors.length > 0) {
      summary += `\n❌ Errors: ${errors.length}`;
    }
    
    if (warnings.length > 0) {
      summary += `\n⚠️ Warnings: ${warnings.length}`;
    }
    
    return summary;
  }
}

export default ArtifactValidator;