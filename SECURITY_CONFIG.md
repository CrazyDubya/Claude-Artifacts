# Security Configuration for Claude Artifacts

## Allowed Dependencies
These packages are pre-approved for use in artifacts:

### UI Libraries
- @radix-ui/*
- lucide-react
- react-icons

### Styling
- clsx
- tailwind-merge
- class-variance-authority

### Utilities
- date-fns
- lodash
- uuid

## Forbidden Patterns
The following patterns are not allowed in artifacts for security reasons:

### Dangerous Functions
- eval()
- Function()
- setTimeout() with string arguments
- setInterval() with string arguments

### DOM Manipulation
- innerHTML
- outerHTML
- document.write()
- insertAdjacentHTML()

### Network Requests
- fetch() to external domains
- XMLHttpRequest to external domains
- Dynamic script loading

### File System Access
- Any Node.js fs operations
- File upload without validation

## Content Security Policy
All artifacts must comply with the following CSP:
- No inline scripts
- No external script sources except approved CDNs
- No eval or unsafe-eval
- Trusted sources only for styles and images

## Validation Rules
1. All imports must be from approved packages
2. No dynamic import() of external URLs
3. All user inputs must be sanitized
4. No server-side code execution from client
5. No access to sensitive browser APIs