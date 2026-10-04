<content>
#!/usr/bin/env python3
"""
Build and diagnostic script for Tent of Trials
Run this after making changes to ensure everything works
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('diagnostic/build.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def create_diagnostic_dir():
    """Create diagnostic directory if it doesn't exist"""
    os.makedirs('diagnostic', exist_ok=True)

def run_linters():
    """Run available linters"""
    logger.info("Running linters...")
    
    results = {
        'flake8': None,
        'pylint': None,
        'mypy': None
    }
    
    # Try flake8
    try:
        result = subprocess.run(['flake8', 'src/', '--count', '--select=E9,F63,F7,F82', '--show-source', '--statistics'], 
                              capture_output=True, text=True)
        results['flake8'] = {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        logger.info(f"Flake8 completed with return code {result.returncode}")
    except FileNotFoundError:
        logger.warning("Flake8 not found, skipping...")
    
    # Try pylint
    try:
        result = subprocess.run(['pylint', 'src/', '--disable=all', '--enable=E,F'], 
                              capture_output=True, text=True)
        results['pylint'] = {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        logger.info(f"Pylint completed with return code {result.returncode}")
    except FileNotFoundError:
        logger.warning("Pylint not found, skipping...")
    
    # Try mypy
    try:
        result = subprocess.run(['mypy', 'src/', '--ignore-missing-imports'], 
                              capture_output=True, text=True)
        results['mypy'] = {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        logger.info(f"MyPy completed with return code {result.returncode}")
    except FileNotFoundError:
        logger.warning("MyPy not found, skipping...")
    
    return results

def check_syntax():
    """Check Python syntax in source files"""
    logger.info("Checking Python syntax...")
    
    syntax_errors = []
    src_dir = Path('src')
    
    for py_file in src_dir.rglob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                compile(f.read(), str(py_file), 'exec')
        except SyntaxError as e:
            syntax_errors.append({
                'file': str(py_file),
                'error': str(e),
                'line': e.lineno
            })
            logger.error(f"Syntax error in {py_file}:{e.lineno}: {e}")
    
    return syntax_errors

def validate_data_files():
    """Validate data files"""
    logger.info("Validating data files...")
    
    issues = []
    data_dir = Path('data')
    
    # Check config.yaml
    config_file = data_dir / 'config.yaml'
    if config_file.exists():
        try:
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
        except Exception as e:
            issues.append({
                'file': str(config_file),
                'error': f"YAML error: {e}"
            })
            logger.error(f"Error in {config_file}: {e}")
    
    return issues

def generate_diagnostics():
    """Generate diagnostic information"""
    logger.info("Generating diagnostics...")
    
    # Basic project info
    project_info = {
        'timestamp': datetime.now().isoformat(),
        'python_version': sys.version,
        'working_directory': os.getcwd(),
        'files': {}
    }
    
    # Count files by type
    for file_path in Path('.').rglob('*'):
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if ext not in project_info['files']:
                project_info['files'][ext] = 0
            project_info['files'][ext] += 1
    
    return project_info

def create_logd_file(diagnostics, linters, syntax_errors, data_issues):
    """Create the .logd diagnostic file"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    logd_file = f'diagnostic/build-{timestamp}.logd'
    
    logd_content = {
        'timestamp': datetime.now().isoformat(),
        'build_info': {
            'python_version': sys.version,
            'working_directory': os.getcwd()
        },
        'linters': linters,
        'syntax_errors': syntax_errors,
        'data_issues': data_issues,
        'diagnostics': diagnostics,
        'summary': {
            'total_files': len(diagnostics['files']) if diagnostics else 0,
            'syntax_errors': len(syntax_errors),
            'data_issues': len(data_issues),
            'linters_passed': sum(1 for l in linters.values() if l and l['returncode'] == 0)
        }
    }
    
    with open(logd_file, 'w') as f:
        f.write("# Tent of Trials Build Diagnostics\n")
        f.write(f"# Generated: {logd_content['timestamp']}\n\n")
        f.write("## Summary\n")
        f.write(f"- Total files: {logd_content['summary']['total_files']}\n")
        f.write(f"- Syntax errors: {logd_content['summary']['syntax_errors']}\n")
        f.write(f"- Data issues: {logd_content['summary']['data_issues']}\n")
        f.write(f"- Linters passed: {logd_content['summary']['linters_passed']}\n\n")
        
        if syntax_errors:
            f.write("## Syntax Errors\n")
            for error in syntax_errors:
                f.write(f"- {error['file']}:{error['line']}: {error['error']}\n")
            f.write("\n")
        
        if data_issues:
            f.write("## Data Issues\n")
            for issue in data_issues:
                f.write(f"- {issue['file']}: {issue['error']}\n")
            f.write("\n")
        
        if linters:
            f.write("## Linter Results\n")
            for linter, result in linters.items():
                if result:
                    f.write(f"### {linter}\n")
                    f.write(f"Return code: {result['returncode']}\n")
                    if result['stdout']:
                        f.write(f"Stdout:\n{result['stdout']}\n")
                    if result['stderr']:
                        f.write(f"Stderr:\n{result['stderr']}\n")
                    f.write("\n")
    
    logger.info(f"Diagnostic log created: {logd_file}")
    return logd_file

def create_json_file(diagnostics, linters, syntax_errors, data_issues):
    """Create the JSON diagnostic file"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_file = f'diagnostic/build-{timestamp}.json'
    
    json_data = {
        'timestamp': datetime.now().isoformat(),
        'build_info': {
            'python_version': sys.version,
            'working_directory': os.getcwd()
        },
        'linters': linters,
        'syntax_errors': syntax_errors,
        'data_issues': data_issues,
        'diagnostics': diagnostics,
        'summary': {
            'total_files': len(diagnostics['files']) if diagnostics else 0,
            'syntax_errors': len(syntax_errors),
            'data_issues': len(data_issues),
            'linters_passed': sum(1 for l in linters.values() if l and l['returncode'] == 0)
        }
    }
    
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    logger.info(f"Diagnostic JSON created: {json_file}")
    return json_file

def main():
    """Main build function"""
    logger.info("Starting build process...")
    
    # Create diagnostic directory
    create_diagnostic_dir()
    
    # Run diagnostics
    linters = run_linters()
    syntax_errors = check_syntax()
    data_issues = validate_data_files()
    diagnostics = generate_diagnostics()
    
    # Create output files
    logd_file = create_logd_file(diagnostics, linters, syntax_errors, data_issues)
    json_file = create_json_file(diagnostics, linters, syntax_errors, data_issues)
    
    # Summary
    logger.info("Build complete!")
    logger.info(f"Log file: {logd_file}")
    logger.info(f"JSON file: {json_file}")
    
    if syntax_errors:
        logger.error(f"Found {len(syntax_errors)} syntax errors")
        sys.exit(1)
    elif data_issues:
        logger.error(f"Found {len(data_issues)} data issues")
        sys.exit(1)
    else:
        logger.info("Build successful!")
        sys.exit(0)

if __name__ == '__main__':
    main()
</content>