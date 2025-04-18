#!/usr/bin/env python3

import re
import os
import requests
from typing import List, Tuple
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def read_changelog(file_path: str) -> str:
    """Read the changelog file content."""
    with open(file_path, 'r') as f:
        return f.read()

def find_pr_references(content: str) -> List[Tuple[str, str]]:
    """Find all PR references in the content and return list of (line, pr_id) tuples."""
    pr_pattern = r'/pull/(\d+)'
    lines = content.split('\n')
    pr_references = []
    
    for line in lines:
        match = re.search(pr_pattern, line)
        if match:
            pr_id = match.group(1)
            pr_references.append((line, pr_id))
    
    return pr_references

def fetch_pr_description(pr_id: str) -> str:
    """Fetch PR description from GitHub API."""
    # Get GitHub token from environment variable
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is not set")
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    url = f'https://api.github.com/repos/woocommerce/woocommerce/pulls/{pr_id}'
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()['body']
    elif response.status_code == 403:
        print(f"Rate limit exceeded. Waiting 60 seconds...")
        time.sleep(60)
        return fetch_pr_description(pr_id)
    else:
        print(f"Error fetching PR {pr_id}: {response.status_code}")
        return ""

def extract_changes_section(description: str) -> str:
    """Extract the 'Changes proposed' section from PR description."""
    pattern = r'Changes proposed in this Pull Request:.*?(?=\n\n|\Z)'
    match = re.search(pattern, description, re.DOTALL)
    if match:
        return match.group(0).strip()
    return ""

def update_changelog(content: str, pr_references: List[Tuple[str, str]]) -> str:
    """Update the changelog content with PR descriptions."""
    lines = content.split('\n')
    updated_lines = []
    
    for line in lines:
        updated_lines.append(line)
        for ref_line, pr_id in pr_references:
            if line == ref_line:
                description = fetch_pr_description(pr_id)
                changes = extract_changes_section(description)
                if changes:
                    updated_lines.append(changes)
                    updated_lines.append('')  # Add blank line for readability
    
    return '\n'.join(updated_lines)

def main():
    # Get the changelog file path from command line argument
    if len(sys.argv) != 2:
        print("Usage: python fetch-pr-descriptions.py <changelog_file>")
        sys.exit(1)
    
    changelog_file = sys.argv[1]
    
    # Read the changelog
    content = read_changelog(changelog_file)
    
    # Find PR references
    pr_references = find_pr_references(content)
    
    # Update the changelog with PR descriptions
    updated_content = update_changelog(content, pr_references)
    
    # Write the updated content back to the file
    with open(changelog_file, 'w') as f:
        f.write(updated_content)
    
    print(f"Updated {len(pr_references)} PR references in {changelog_file}")

if __name__ == '__main__':
    import sys
    main()
