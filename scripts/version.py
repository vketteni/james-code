#!/usr/bin/env python3
"""Version management script for james-code package."""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple


def run_command(cmd: str, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    return subprocess.run(
        cmd, shell=True, capture_output=capture_output, text=True, check=True
    )


def get_current_version() -> str:
    """Get the current version from git tags."""
    try:
        result = run_command("git describe --tags --abbrev=0")
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "0.0.0"


def get_next_version(current_version: str, bump_type: str) -> str:
    """Calculate the next version based on bump type."""
    # Remove 'v' prefix if present
    version = current_version.lstrip('v')
    
    # Parse version components
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)', version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    
    major, minor, patch = map(int, match.groups())
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")
    
    return f"{major}.{minor}.{patch}"


def create_tag(version: str, message: Optional[str] = None) -> None:
    """Create a git tag for the given version."""
    tag_name = f"v{version}"
    
    if message is None:
        message = f"Release {tag_name}"
    
    run_command(f'git tag -a "{tag_name}" -m "{message}"', capture_output=False)
    print(f"Created tag: {tag_name}")


def list_tags() -> None:
    """List all version tags."""
    try:
        result = run_command("git tag -l --sort=-version:refname")
        tags = result.stdout.strip().split('\n')
        if tags and tags[0]:
            print("Available tags:")
            for tag in tags:
                print(f"  {tag}")
        else:
            print("No tags found.")
    except subprocess.CalledProcessError:
        print("No tags found.")


def get_current_commit_info() -> Tuple[str, str]:
    """Get current commit hash and message."""
    commit_hash = run_command("git rev-parse --short HEAD").stdout.strip()
    commit_msg = run_command("git log -1 --pretty=%s").stdout.strip()
    return commit_hash, commit_msg


def check_git_status() -> bool:
    """Check if working directory is clean."""
    try:
        result = run_command("git status --porcelain")
        return len(result.stdout.strip()) == 0
    except subprocess.CalledProcessError:
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Version management for james-code")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Current version
    subparsers.add_parser("current", help="Show current version")
    
    # List tags
    subparsers.add_parser("list", help="List all version tags")
    
    # Tag creation
    tag_parser = subparsers.add_parser("tag", help="Create a new version tag")
    tag_parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch"],
        help="Type of version bump"
    )
    tag_parser.add_argument(
        "-m", "--message",
        help="Tag message (optional)"
    )
    tag_parser.add_argument(
        "--force",
        action="store_true",
        help="Force tag creation even with uncommitted changes"
    )
    
    # Direct tag
    direct_parser = subparsers.add_parser("direct", help="Create tag with specific version")
    direct_parser.add_argument("version", help="Version to tag (e.g., 1.0.0)")
    direct_parser.add_argument(
        "-m", "--message",
        help="Tag message (optional)"
    )
    direct_parser.add_argument(
        "--force",
        action="store_true",
        help="Force tag creation even with uncommitted changes"
    )
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    try:
        if args.command == "current":
            current = get_current_version()
            commit_hash, commit_msg = get_current_commit_info()
            print(f"Current version: {current}")
            print(f"Current commit: {commit_hash} - {commit_msg}")
        
        elif args.command == "list":
            list_tags()
        
        elif args.command == "tag":
            if not args.force and not check_git_status():
                print("Error: Working directory is not clean. Commit changes first or use --force")
                sys.exit(1)
            
            current = get_current_version()
            next_version = get_next_version(current, args.bump_type)
            
            print(f"Current version: {current}")
            print(f"Next version: {next_version}")
            
            create_tag(next_version, args.message)
        
        elif args.command == "direct":
            if not args.force and not check_git_status():
                print("Error: Working directory is not clean. Commit changes first or use --force")
                sys.exit(1)
            
            create_tag(args.version, args.message)
    
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()