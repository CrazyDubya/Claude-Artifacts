# Contributing to Claude Artifacts

Thank you for your interest in contributing to Claude Artifacts! This document provides guidelines for contributing to the project.

## 🤝 Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## 🎯 How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- **Clear description** of the issue
- **Steps to reproduce** the behavior
- **Expected behavior** vs actual behavior
- **Screenshots** if applicable
- **Environment details** (OS, Node version, etc.)
- **Error messages** or console output

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear description** of the enhancement
- **Use case** explaining why this would be useful
- **Possible implementation** if you have ideas
- **Alternative solutions** you've considered

### Security Issues

**DO NOT** report security vulnerabilities through public GitHub issues. Instead, please review [SECURITY_CONFIG.md](SECURITY_CONFIG.md) and follow the security reporting guidelines.

## 🔧 Development Process

### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Claude-Artifacts.git
   cd Claude-Artifacts
   ```

3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Install dependencies**:
   ```bash
   cd app-analyzer
   npm install
   ```

### Making Changes

1. **Follow the code style**:
   - Use ESLint configuration provided
   - Follow React best practices
   - Use meaningful variable and function names
   - Add comments for complex logic

2. **Security requirements**:
   - All artifacts MUST pass security validation
   - No use of `eval()`, `Function()`, or `innerHTML`
   - Only approved dependencies (see README.md)
   - Sanitize all user inputs
   - Use proper error boundaries

3. **Test your changes**:
   ```bash
   # Run the artifact manager
   python3 artifact_manager.py
   
   # Test your artifact loads without errors
   # Verify security validation passes
   ```

4. **Update documentation**:
   - Update README.md if adding features
   - Add JSDoc comments to functions
   - Update AUDIT_REPORT.md if fixing security issues

### Creating Artifacts

When contributing new artifacts:

1. **Place in correct directory**: `app-analyzer/src/claude_artifacts/`

2. **Use security-approved patterns**:
   ```jsx
   import React, { useState, useCallback, useMemo } from 'react';
   import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
   
   const YourArtifact = () => {
     // Use hooks properly
     const [state, setState] = useState(initialValue);
     
     // Memoize callbacks
     const handleAction = useCallback(() => {
       // Implementation
     }, [dependencies]);
     
     return (
       <Card>
         <CardHeader>
           <CardTitle>Your Artifact Title</CardTitle>
         </CardHeader>
         <CardContent>
           {/* Your content */}
         </CardContent>
       </Card>
     );
   };
   
   export default YourArtifact;
   ```

3. **Include metadata**:
   ```jsx
   // At the top of your file
   /**
    * Artifact Name: Your Artifact
    * Description: Brief description of what it does
    * Author: Your Name
    * Security Level: Validated
    * Dependencies: @/components/ui/card, lucide-react
    */
   ```

### Commit Guidelines

1. **Write clear commit messages**:
   ```
   feat: Add new color picker component
   fix: Resolve security validation for date-fns
   docs: Update installation instructions
   security: Fix XSS vulnerability in input handler
   ```

2. **Use conventional commit format**:
   - `feat`: New feature
   - `fix`: Bug fix
   - `docs`: Documentation only
   - `style`: Formatting, missing semicolons, etc.
   - `refactor`: Code restructuring
   - `perf`: Performance improvements
   - `test`: Adding tests
   - `security`: Security-related changes
   - `chore`: Maintenance tasks

3. **Keep commits focused**:
   - One logical change per commit
   - Don't mix refactoring with features
   - Split large changes into smaller commits

### Pull Request Process

1. **Update your branch**:
   ```bash
   git fetch upstream
   git rebase upstream/master
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request**:
   - Use a clear, descriptive title
   - Reference related issues
   - Provide detailed description of changes
   - Include screenshots for UI changes
   - List testing performed
   - Confirm security validation passed

4. **PR Template**:
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   - [ ] Security fix
   
   ## Testing
   - [ ] Tested locally
   - [ ] Security validation passed
   - [ ] No console errors
   - [ ] Works in multiple browsers
   
   ## Screenshots (if applicable)
   
   ## Related Issues
   Closes #issue_number
   ```

5. **Review process**:
   - Address review comments promptly
   - Push new commits to update PR
   - Re-request review after changes
   - Be open to feedback and suggestions

## 📋 Checklist for Contributors

Before submitting your PR, ensure:

- [ ] Code follows project style guidelines
- [ ] Security validation passes for all artifacts
- [ ] No console errors or warnings
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] PR description is complete
- [ ] Tests pass (if applicable)
- [ ] No merge conflicts
- [ ] Screenshots included for UI changes

## 🎨 Code Style Guidelines

### JavaScript/React

```javascript
// Good
const MyComponent = () => {
  const [isActive, setIsActive] = useState(false);
  
  const handleClick = useCallback(() => {
    setIsActive(prev => !prev);
  }, []);
  
  return (
    <button onClick={handleClick}>
      {isActive ? 'Active' : 'Inactive'}
    </button>
  );
};

// Bad
const MyComponent = () => {
  const [isActive, setIsActive] = useState(false);
  
  return (
    <button onClick={() => setIsActive(!isActive)}>
      {isActive ? 'Active' : 'Inactive'}
    </button>
  );
};
```

### Python

```python
# Good
def analyze_artifact(artifact_path: str) -> dict:
    """
    Analyze an artifact for security issues.
    
    Args:
        artifact_path: Path to the artifact file
        
    Returns:
        Dictionary with analysis results
    """
    return validate_security(artifact_path)

# Bad
def analyze_artifact(artifact_path):
    return validate_security(artifact_path)
```

## 🔒 Security Guidelines

1. **Never use dangerous patterns**:
   - `eval()`, `Function()`
   - `innerHTML`, `outerHTML`
   - `document.write()`
   - Inline event handlers in JSX

2. **Always sanitize inputs**:
   ```javascript
   // Good
   const sanitizedValue = DOMPurify.sanitize(userInput);
   
   // Bad
   element.innerHTML = userInput;
   ```

3. **Use approved dependencies only**:
   - Check README.md for allowed packages
   - Request approval for new dependencies
   - Provide security justification

## 🧪 Testing

### Manual Testing

1. **Load your artifact** in the application
2. **Test all interactive features**
3. **Check browser console** for errors
4. **Verify security validation** passes
5. **Test error handling** (try breaking it)

### Security Testing

```bash
# Run security validation
python3 artifact_manager.py

# Check for security issues
grep -r "innerHTML\|eval\|Function" app-analyzer/src/
```

## 📚 Resources

- [React Best Practices](https://react.dev/learn)
- [Security Guidelines](SECURITY_CONFIG.md)
- [Security Audit Report](AUDIT_REPORT.md)
- [Project Structure](README.md#-project-structure)

## ❓ Questions?

- **General questions**: Open a GitHub Discussion
- **Bug reports**: Create a GitHub Issue
- **Security concerns**: Follow security reporting guidelines
- **Feature requests**: Open a GitHub Issue with [Feature Request] tag

## 🙏 Recognition

Contributors will be recognized in:
- Project README.md
- Release notes
- GitHub contributors page

Thank you for helping make Claude Artifacts better and more secure!

---

**Remember**: Security first, user experience second, performance third. Never compromise on security for convenience.
