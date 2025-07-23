#!/usr/bin/env python3
"""
Comprehensive validation and testing script for Claude Artifacts Repository
Performs security checks, code quality analysis, and functional testing
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
import tempfile
import shutil

class ArtifactTester:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.app_dir = self.root_dir / "app-analyzer"
        self.src_dir = self.app_dir / "src"
        self.artifacts_dir = self.src_dir / "claude_artifacts"
        self.results = {
            "security": {},
            "quality": {},
            "performance": {},
            "functionality": {}
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        print("🔍 Starting comprehensive validation suite...")
        
        # Security tests
        print("\n🔒 Running security validation...")
        self.test_security()
        
        # Code quality tests
        print("\n🛠️ Running code quality checks...")
        self.test_code_quality()
        
        # Performance tests
        print("\n⚡ Running performance analysis...")
        self.test_performance()
        
        # Functionality tests
        print("\n🧪 Running functionality tests...")
        self.test_functionality()
        
        # Generate report
        self.generate_report()
        
        return self.results

    def test_security(self):
        """Comprehensive security validation"""
        security_results = {
            "shell_injection": self.check_shell_injection(),
            "xss_vulnerabilities": self.check_xss_vulnerabilities(),
            "unsafe_imports": self.check_unsafe_imports(),
            "path_traversal": self.check_path_traversal(),
            "dangerous_patterns": self.check_dangerous_patterns()
        }
        
        self.results["security"] = security_results
        
        # Calculate security score
        passed = sum(1 for result in security_results.values() if result["status"] == "PASS")
        total = len(security_results)
        score = (passed / total) * 10
        self.results["security"]["score"] = score
        
        print(f"   Security Score: {score:.1f}/10")

    def check_shell_injection(self) -> Dict[str, Any]:
        """Check for shell injection vulnerabilities"""
        issues = []
        
        # Check Python files for actual shell=True usage (not in comments)
        for py_file in self.root_dir.rglob("*.py"):
            # Skip test files
            if "test" in py_file.name.lower():
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines, 1):
                        # Skip comments
                        if line.strip().startswith('#'):
                            continue
                        # Check for shell=True not in comment
                        if "shell=True" in line and not "#" in line.split("shell=True")[0]:
                            issues.append(f"Shell injection risk in {py_file}:{i}")
            except Exception as e:
                issues.append(f"Could not read {py_file}: {e}")
        
        return {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "description": "Check for shell injection vulnerabilities"
        }

    def check_xss_vulnerabilities(self) -> Dict[str, Any]:
        """Check for XSS vulnerabilities"""
        issues = []
        dangerous_patterns = [
            r'\.innerHTML\s*=',
            r'dangerouslySetInnerHTML',
            r'document\.write\s*\(',
            r'insertAdjacentHTML\s*\('
        ]
        
        for js_file in self.src_dir.rglob("*.{js,jsx}"):
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for pattern in dangerous_patterns:
                        if re.search(pattern, content):
                            issues.append(f"Potential XSS in {js_file}: {pattern}")
            except Exception as e:
                issues.append(f"Could not read {js_file}: {e}")
        
        return {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "description": "Check for XSS vulnerabilities"
        }

    def check_unsafe_imports(self) -> Dict[str, Any]:
        """Check for unsafe imports"""
        issues = []
        allowed_packages = [
            "@radix-ui", "lucide-react", "react-icons", "clsx", 
            "tailwind-merge", "class-variance-authority", "date-fns", 
            "lodash", "uuid", "react", "react-dom"
        ]
        
        for js_file in self.artifacts_dir.rglob("*.{js,jsx}"):
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Find all imports
                    import_pattern = r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]'
                    imports = re.findall(import_pattern, content)
                    
                    for imp in imports:
                        # Skip relative imports
                        if imp.startswith('./') or imp.startswith('../') or imp.startsWith('@/'):
                            continue
                            
                        # Check if allowed
                        is_allowed = any(imp.startswith(allowed) for allowed in allowed_packages)
                        if not is_allowed:
                            issues.append(f"Unauthorized import in {js_file}: {imp}")
                            
            except Exception as e:
                issues.append(f"Could not read {js_file}: {e}")
        
        return {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "description": "Check for unauthorized imports"
        }

    def check_path_traversal(self) -> Dict[str, Any]:
        """Check for path traversal vulnerabilities"""
        issues = []
        
        # Check for hardcoded paths
        for py_file in self.root_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Look for absolute paths that might be hardcoded
                    if "/Users/" in content or "/home/" in content:
                        if "pup/reactclaude" not in content:  # Old hardcoded path should be gone
                            issues.append(f"Potential hardcoded path in {py_file}")
            except Exception as e:
                issues.append(f"Could not read {py_file}: {e}")
        
        return {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "description": "Check for path traversal vulnerabilities"
        }

    def check_dangerous_patterns(self) -> Dict[str, Any]:
        """Check for other dangerous patterns"""
        issues = []
        dangerous_patterns = [
            (r'\beval\s*\(', "eval() usage"),
            (r'\bFunction\s*\(', "Function() constructor"),
            (r'setTimeout\s*\(\s*[\'"]', "setTimeout with string"),
            (r'setInterval\s*\(\s*[\'"]', "setInterval with string")
        ]
        
        for js_file in self.src_dir.rglob("*.{js,jsx}"):
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for pattern, description in dangerous_patterns:
                        if re.search(pattern, content):
                            issues.append(f"{description} in {js_file}")
            except Exception as e:
                issues.append(f"Could not read {js_file}: {e}")
        
        return {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "description": "Check for dangerous coding patterns"
        }

    def test_code_quality(self):
        """Test code quality metrics"""
        quality_results = {
            "error_boundaries": self.check_error_boundaries(),
            "import_consistency": self.check_import_consistency(),
            "component_structure": self.check_component_structure(),
            "documentation": self.check_documentation()
        }
        
        self.results["quality"] = quality_results
        
        # Calculate quality score
        passed = sum(1 for result in quality_results.values() if result["status"] == "PASS")
        total = len(quality_results)
        score = (passed / total) * 10
        self.results["quality"]["score"] = score
        
        print(f"   Code Quality Score: {score:.1f}/10")

    def check_error_boundaries(self) -> Dict[str, Any]:
        """Check for proper error boundary usage"""
        issues = []
        has_error_boundary = False
        
        # Check if ErrorBoundary component exists
        error_boundary_file = self.src_dir / "components" / "ErrorBoundary.jsx"
        if error_boundary_file.exists():
            has_error_boundary = True
        else:
            issues.append("ErrorBoundary component not found")
        
        # Check if it's being used
        if has_error_boundary:
            loader_file = self.src_dir / "components" / "ArtifactLoader.jsx"
            if loader_file.exists():
                try:
                    with open(loader_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if "ErrorBoundary" not in content:
                            issues.append("ErrorBoundary not used in ArtifactLoader")
                except Exception as e:
                    issues.append(f"Could not read ArtifactLoader: {e}")
        
        return {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "description": "Check for error boundary implementation"
        }

    def check_import_consistency(self) -> Dict[str, Any]:
        """Check for consistent import patterns"""
        issues = []
        
        for js_file in self.artifacts_dir.rglob("*.jsx"):
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check for .jsx extensions in imports (inconsistent)
                    if re.search(r'from\s+[\'"][^\'"]*/[^\'"]\.jsx[\'"]', content):
                        issues.append(f"Inconsistent .jsx extension in imports: {js_file}")
                        
            except Exception as e:
                issues.append(f"Could not read {js_file}: {e}")
        
        return {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "description": "Check for consistent import patterns"
        }

    def check_component_structure(self) -> Dict[str, Any]:
        """Check React component structure"""
        issues = []
        
        for js_file in self.artifacts_dir.rglob("*.jsx"):
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check for default export
                    if "export default" not in content:
                        issues.append(f"Missing default export: {js_file}")
                    
                    # Check for React import
                    if "import React" not in content and "import.*React" not in content:
                        issues.append(f"Missing React import: {js_file}")
                        
            except Exception as e:
                issues.append(f"Could not read {js_file}: {e}")
        
        return {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "description": "Check React component structure"
        }

    def check_documentation(self) -> Dict[str, Any]:
        """Check documentation quality"""
        issues = []
        
        # Check for key documentation files
        required_docs = ["README.md", "AUDIT_REPORT.md", "SECURITY_CONFIG.md"]
        for doc in required_docs:
            if not (self.root_dir / doc).exists():
                issues.append(f"Missing documentation: {doc}")
        
        return {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "description": "Check documentation completeness"
        }

    def test_performance(self):
        """Test performance characteristics"""
        performance_results = {
            "optimization_patterns": self.check_optimization_patterns(),
            "bundle_analysis": self.check_bundle_characteristics()
        }
        
        self.results["performance"] = performance_results
        
        # Calculate performance score
        passed = sum(1 for result in performance_results.values() if result["status"] == "PASS")
        total = len(performance_results)
        score = (passed / total) * 10
        self.results["performance"]["score"] = score
        
        print(f"   Performance Score: {score:.1f}/10")

    def check_optimization_patterns(self) -> Dict[str, Any]:
        """Check for React optimization patterns"""
        issues = []
        optimizations_found = []
        
        loader_file = self.src_dir / "components" / "ArtifactLoader.jsx"
        if loader_file.exists():
            try:
                with open(loader_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check for useCallback
                    if "useCallback" in content:
                        optimizations_found.append("useCallback")
                    else:
                        issues.append("Missing useCallback optimization")
                    
                    # Check for useMemo
                    if "useMemo" in content:
                        optimizations_found.append("useMemo")
                    
                    # Check for React.memo (would need to check imports)
                    if "React.memo" in content or "memo" in content:
                        optimizations_found.append("memo")
                        
            except Exception as e:
                issues.append(f"Could not analyze ArtifactLoader: {e}")
        
        return {
            "status": "PASS" if len(optimizations_found) >= 1 else "WARN",
            "issues": issues,
            "optimizations": optimizations_found,
            "description": "Check for React optimization patterns"
        }

    def check_bundle_characteristics(self) -> Dict[str, Any]:
        """Analyze bundle characteristics"""
        issues = []
        
        # Check if package.json exists and has reasonable dependencies
        package_json = self.app_dir / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    deps = data.get("dependencies", {})
                    dev_deps = data.get("devDependencies", {})
                    
                    total_deps = len(deps) + len(dev_deps)
                    if total_deps > 50:
                        issues.append(f"High dependency count: {total_deps}")
                    
            except Exception as e:
                issues.append(f"Could not analyze package.json: {e}")
        else:
            issues.append("package.json not found")
        
        return {
            "status": "PASS" if not issues else "WARN",
            "issues": issues,
            "description": "Analyze bundle characteristics"
        }

    def test_functionality(self):
        """Test basic functionality"""
        functionality_results = {
            "artifact_manager": self.test_artifact_manager(),
            "artifact_loading": self.test_artifact_loading(),
            "validator_functionality": self.test_validator()
        }
        
        self.results["functionality"] = functionality_results
        
        # Calculate functionality score
        passed = sum(1 for result in functionality_results.values() if result["status"] == "PASS")
        total = len(functionality_results)
        score = (passed / total) * 10
        self.results["functionality"]["score"] = score
        
        print(f"   Functionality Score: {score:.1f}/10")

    def test_artifact_manager(self) -> Dict[str, Any]:
        """Test artifact manager functionality"""
        issues = []
        
        manager_file = self.app_dir / "artifact_manager.py"
        if not manager_file.exists():
            return {
                "status": "FAIL",
                "issues": ["artifact_manager.py not found"],
                "description": "Test artifact manager"
            }
        
        # Try to import and basic syntax check
        try:
            # Run syntax check
            result = subprocess.run([
                sys.executable, "-m", "py_compile", str(manager_file)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                issues.append(f"Syntax error in artifact_manager.py: {result.stderr}")
                
        except Exception as e:
            issues.append(f"Could not test artifact_manager.py: {e}")
        
        return {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "description": "Test artifact manager functionality"
        }

    def test_artifact_loading(self) -> Dict[str, Any]:
        """Test artifact loading mechanism"""
        issues = []
        artifacts_found = 0
        
        # Count artifacts
        for artifact_file in self.artifacts_dir.rglob("*.jsx"):
            artifacts_found += 1
            
            # Basic syntax/structure check
            try:
                with open(artifact_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    if "export default" not in content:
                        issues.append(f"No default export in {artifact_file}")
                        
            except Exception as e:
                issues.append(f"Could not read {artifact_file}: {e}")
        
        if artifacts_found == 0:
            issues.append("No artifacts found")
        
        return {
            "status": "PASS" if not issues and artifacts_found > 0 else "FAIL",
            "issues": issues,
            "artifacts_count": artifacts_found,
            "description": "Test artifact loading mechanism"
        }

    def test_validator(self) -> Dict[str, Any]:
        """Test validator functionality"""
        issues = []
        
        validator_file = self.src_dir / "services" / "artifactValidator.js"
        if not validator_file.exists():
            return {
                "status": "FAIL",
                "issues": ["artifactValidator.js not found"],
                "description": "Test validator functionality"
            }
        
        # Check validator structure
        try:
            with open(validator_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                required_methods = ["validate", "validateImports", "checkForXSS"]
                for method in required_methods:
                    if method not in content:
                        issues.append(f"Missing method: {method}")
                        
        except Exception as e:
            issues.append(f"Could not analyze validator: {e}")
        
        return {
            "status": "PASS" if not issues else "FAIL",
            "issues": issues,
            "description": "Test validator functionality"
        }

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("🎯 COMPREHENSIVE VALIDATION REPORT")
        print("="*60)
        
        # Overall scores
        overall_score = (
            self.results["security"]["score"] +
            self.results["quality"]["score"] +
            self.results["performance"]["score"] +
            self.results["functionality"]["score"]
        ) / 4
        
        print(f"\n📊 OVERALL SCORE: {overall_score:.1f}/10")
        print(f"🔒 Security: {self.results['security']['score']:.1f}/10")
        print(f"🛠️ Quality: {self.results['quality']['score']:.1f}/10")
        print(f"⚡ Performance: {self.results['performance']['score']:.1f}/10")
        print(f"🧪 Functionality: {self.results['functionality']['score']:.1f}/10")
        
        # Detailed results
        for category, results in self.results.items():
            if category == "score":
                continue
                
            print(f"\n{category.upper()} DETAILS:")
            print("-" * 30)
            
            for test_name, test_result in results.items():
                if test_name == "score":
                    continue
                    
                status = test_result.get("status", "UNKNOWN")
                status_emoji = "✅" if status == "PASS" else "⚠️" if status == "WARN" else "❌"
                
                print(f"{status_emoji} {test_name}: {status}")
                
                if test_result.get("issues"):
                    for issue in test_result["issues"][:3]:  # Limit to first 3 issues
                        print(f"    • {issue}")
                    if len(test_result["issues"]) > 3:
                        print(f"    • ... and {len(test_result['issues']) - 3} more")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        print("-" * 30)
        
        if overall_score >= 8.0:
            print("✅ Excellent! The codebase meets high security and quality standards.")
        elif overall_score >= 6.0:
            print("⚠️ Good progress, but some improvements needed.")
        else:
            print("❌ Significant improvements required for production readiness.")
        
        print("\n📝 NEXT STEPS:")
        print("1. Address any FAIL status items immediately")
        print("2. Review and fix WARN status items")
        print("3. Run tests again to verify improvements")
        print("4. Consider adding automated testing to CI/CD pipeline")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = os.getcwd()
    
    tester = ArtifactTester(root_dir)
    results = tester.run_all_tests()
    
    # Save results to file
    results_file = Path(root_dir) / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")


if __name__ == "__main__":
    main()