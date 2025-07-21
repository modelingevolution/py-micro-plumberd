#!/usr/bin/env python3
"""Script to bump version in pyproject.toml and __init__.py"""

import sys
import re
from pathlib import Path

def bump_version(version_type):
    """Bump version in pyproject.toml and __init__.py
    
    Args:
        version_type: 'patch', 'minor', or 'major'
    """
    
    # Read pyproject.toml
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    
    # Find current version
    version_match = re.search(r'version = "(\d+)\.(\d+)\.(\d+)"', content)
    if not version_match:
        print("Could not find version in pyproject.toml")
        return False
    
    major, minor, patch = map(int, version_match.groups())
    
    # Bump version
    if version_type == "patch":
        patch += 1
    elif version_type == "minor":
        minor += 1
        patch = 0
    elif version_type == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        print(f"Invalid version type: {version_type}")
        return False
    
    new_version = f"{major}.{minor}.{patch}"
    print(f"Bumping version from {version_match.group(1)}.{version_match.group(2)}.{version_match.group(3)} to {new_version}")
    
    # Update pyproject.toml
    new_content = re.sub(
        r'version = "\d+\.\d+\.\d+"',
        f'version = "{new_version}"',
        content
    )
    pyproject_path.write_text(new_content)
    
    # Update __init__.py
    init_path = Path("py_micro_plumberd/__init__.py")
    if init_path.exists():
        init_content = init_path.read_text()
        new_init_content = re.sub(
            r'__version__ = "\d+\.\d+\.\d+"',
            f'__version__ = "{new_version}"',
            init_content
        )
        init_path.write_text(new_init_content)
    
    print(f"Updated version to {new_version}")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/bump_version.py <patch|minor|major>")
        sys.exit(1)
    
    version_type = sys.argv[1]
    if bump_version(version_type):
        print("Version bumped successfully!")
        print("Don't forget to:")
        print("1. git add pyproject.toml py_micro_plumberd/__init__.py")
        print("2. git commit -m 'Bump version to X.Y.Z'")
        print("3. git tag vX.Y.Z")
        print("4. git push origin main --tags")
        print("5. Create a GitHub release")
    else:
        sys.exit(1)