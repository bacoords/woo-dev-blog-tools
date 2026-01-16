#!/usr/bin/env python3
"""
Fetch WooCommerce release data for analysis.

This script fetches changelog and release post data, preparing it for
analysis using Claude skills:
- /woocommerce-pr-analyzer <version> - Full thematic analysis
- /woocommerce-release-comms <version> - Quick relevance scoring
"""

import subprocess
from pathlib import Path
import argparse
import sys


def run_script(script_name, *args):
    """Run a Python script and return True if successful."""
    try:
        subprocess.run([sys.executable, script_name, *args], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
        return False


def check_changelog_exists(version):
    """Check if changelog file exists for the specified version."""
    possible_paths = [
        Path(f'changelogs/{version}.csv'),
        Path(f'changelogs/{version}.0.csv'),
        Path(f'changelogs/{version.rstrip(".0")}.csv'),
        Path(f'changelogs/{version}.txt'),
        Path(f'changelogs/{version}.0.txt'),
        Path(f'changelogs/{version.rstrip(".0")}.txt'),
    ]

    for path in possible_paths:
        if path.exists():
            return path
    return None


def check_release_posts_exist():
    """Check if release posts directory has content."""
    release_posts_dir = Path('release-posts')
    if not release_posts_dir.exists():
        return False
    files = list(release_posts_dir.glob('*.txt'))
    return len(files) > 0


def main():
    parser = argparse.ArgumentParser(
        description='Fetch WooCommerce release data for Claude analysis',
        epilog='''
After fetching data, analyze with Claude skills:
  /woocommerce-pr-analyzer <version>   - Full thematic analysis
  /woocommerce-release-comms <version> - Quick relevance scoring
        '''
    )
    parser.add_argument('--fetch-posts', action='store_true',
                       help='Fetch release posts from developer blog')
    parser.add_argument('--fetch-changelog', action='store_true',
                       help='Fetch changelog from GitHub')
    parser.add_argument('--version', type=str,
                       help='WooCommerce version (e.g. 9.9.0)')
    parser.add_argument('--check', action='store_true',
                       help='Check if required data files exist')
    args = parser.parse_args()

    # Get version input if not provided as argument
    version = args.version
    if not version and (args.fetch_changelog or args.check):
        version = input("Enter WooCommerce version (e.g. 9.9.0): ")

    # Check mode - just verify files exist
    if args.check:
        print(f"\nChecking data files for version {version}...")

        changelog_path = check_changelog_exists(version)
        if changelog_path:
            print(f"  Changelog: {changelog_path}")
        else:
            print(f"  Changelog: NOT FOUND")
            print(f"    Run: python fetch-changelog.py {version}")

        if check_release_posts_exist():
            print(f"  Release posts: release-posts/ (found)")
        else:
            print(f"  Release posts: NOT FOUND")
            print(f"    Run: python fetch-posts.py")

        if changelog_path and check_release_posts_exist():
            print(f"\nData ready! Analyze with:")
            print(f"  /woocommerce-pr-analyzer {version}")
            print(f"  /woocommerce-release-comms {version}")
        return

    # Fetch release posts if requested
    if args.fetch_posts:
        print("Fetching release posts...")
        if not run_script('fetch-posts.py'):
            print("Failed to fetch release posts")
            return

    # Fetch changelog if requested
    if args.fetch_changelog:
        if not version:
            print("Error: --version required when using --fetch-changelog")
            return
        print(f"Fetching changelog for version {version}...")
        if not run_script('fetch-changelog.py', version):
            print("Failed to fetch changelog")
            return

    # If no flags provided, show help
    if not args.fetch_posts and not args.fetch_changelog and not args.check:
        parser.print_help()
        print("\n" + "=" * 60)
        print("Quick Start:")
        print("=" * 60)
        print(f"\n1. Fetch data:")
        print(f"   python audit-release-prs.py --fetch-changelog --fetch-posts --version 9.9.0")
        print(f"\n2. Analyze with Claude:")
        print(f"   /woocommerce-pr-analyzer 9.9.0")
        print(f"\n3. Or for quick scoring:")
        print(f"   /woocommerce-release-comms 9.9.0")
        return

    # Show next steps
    print("\n" + "=" * 60)
    print("Data fetched successfully!")
    print("=" * 60)

    if version:
        changelog_path = check_changelog_exists(version)
        if changelog_path:
            print(f"\nChangelog: {changelog_path}")

    if check_release_posts_exist():
        print(f"Release posts: release-posts/")

    print(f"\nNext steps - analyze with Claude:")
    if version:
        print(f"  /woocommerce-pr-analyzer {version}   - Full thematic analysis")
        print(f"  /woocommerce-release-comms {version} - Quick relevance scoring")
    else:
        print(f"  /woocommerce-pr-analyzer <version>   - Full thematic analysis")
        print(f"  /woocommerce-release-comms <version> - Quick relevance scoring")


if __name__ == "__main__":
    main()
