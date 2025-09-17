import requests
import re
import os
import sys
import time
import csv
from dotenv import load_dotenv
from html import unescape

# Load environment variables from .env file
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "woocommerce"
REPO_NAME = "woocommerce"

def fetch_changelog(version):
    # Use the trunk changelog URL
    changelog_url = "https://raw.githubusercontent.com/woocommerce/woocommerce/refs/heads/trunk/changelog.txt"

    try:
        # Fetch the changelog
        response = requests.get(changelog_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Get the content and split at the changelog marker
        content = response.text
        
        # Find the specific version section
        version_marker = f"= {version} "
        if version_marker not in content:
            print(f"Changelog section for version {version} not found. Attempting to generate from GitHub API...")
            return fetch_prs_from_github(version)
            
        # Split at the version marker and get the content up to the next version
        parts = content.split(version_marker)
        if len(parts) < 2:
            print(f"Error: Could not find changelog section for version {version}")
            return False
            
        # Get the content up to the next version marker
        changelog_content = parts[1].split("= ")[0].strip()
        
        # Save the changelog to a file
        save_changelog(version, changelog_content)
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error fetching changelog: {e}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def fetch_prs_from_github(version):
    """Fetch PRs from GitHub API for the specified milestone. If test_mode, only fetch 10 PRs."""
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable is not set")
        return False
        
    # First verify the milestone exists
    milestone_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/milestones"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # Get all milestones to find the correct one
        response = requests.get(milestone_url, headers=headers)
        if response.status_code == 403:
            print("Error: GitHub API rate limit exceeded. Please try again later.")
            return False
        response.raise_for_status()
        milestones = response.json()
        
        # Find the milestone that matches our version
        milestone_number = None
        for milestone in milestones:
            if milestone['title'] == version:
                milestone_number = milestone['number']
                print(f"Found milestone {version} with number {milestone_number}")
                break
        
        if not milestone_number:
            print(f"Warning: Could not find milestone for version {version}")
            print("Available milestones:")
            for m in milestones:
                print(f"- {m['title']}")
            return False

        # Now fetch PRs with the correct milestone number
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"  # Use issues endpoint instead of pulls
        params = {
            "state": "closed",
            "milestone": str(milestone_number),
            "per_page": 100
        }

        all_prs = []
        next_url = url
        page_count = 0

        while next_url:
            page_count += 1
            print(f"Fetching PRs from page {page_count}...")
            response = requests.get(next_url, headers=headers, params=params)
            response.raise_for_status()
            issues = response.json()

            if not issues:
                print("No more PRs found, stopping pagination.")
                break

            # Filter to only include PRs (issues with pull_request field)
            prs = [issue for issue in issues if 'pull_request' in issue]
            print(f"Found {len(prs)} PRs on this page")
            all_prs.extend(prs)

            # Get the next page URL from the Link header
            link_header = response.headers.get('Link', '')
            if link_header:
                # Parse the Link header to find the 'next' URL
                for link in link_header.split(','):
                    if 'rel="next"' in link:
                        next_url = link.split(';')[0].strip('<>')
                        break
                else:
                    next_url = None
            else:
                next_url = None
                
            if not next_url:
                print("No more pages available")
                break
                
            # Clear params as they're included in the next_url
            params = {}

        print(f"Total PRs found: {len(all_prs)}")
        if not all_prs:
            print(f"No PRs found for milestone {version}.")
            return False

        # Format PRs into changelog format
        changelog_rows = format_prs_as_changelog(all_prs)
        save_changelog(version, changelog_rows)
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error fetching PRs from GitHub: {e}")
        return False

def extract_changes_section(description: str) -> str:
    """Extract the 'Changes proposed' section from PR description, stripping HTML tags and stopping at the testing section."""
    if not description:
        return ""
        
    # First strip any HTML tags
    description = re.sub(r'<[^>]+>', '', description)
    # Unescape any HTML entities
    description = unescape(description)
    
    # Find content between "Changes proposed" and "How to test"
    pattern = r'Changes proposed in this Pull Request:(.*?)(?=How to test the changes in this Pull Request:|\Z)'
    match = re.search(pattern, description, re.DOTALL)
    if match:
        # Get the captured group (content between the markers)
        content = match.group(1)
        # Clean up the content:
        # 1. Remove any leading/trailing whitespace
        # 2. Remove any empty lines
        # 3. Remove any lines that are just comments
        lines = [line.strip() for line in content.split('\n')]
        lines = [line for line in lines if line and not line.startswith('<!--') and not line.endswith('-->')]
        return '\n'.join(lines).strip()
    return ""

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
        return extract_changes_section( response.json()['body'] )
    elif response.status_code == 403:
        print(f"Rate limit exceeded. Waiting 60 seconds...")
        time.sleep(60)
        return fetch_pr_description(pr_id)
    else:
        print(f"Error fetching PR {pr_id}: {response.status_code}")
        return ""

def format_prs_as_changelog(prs):
    """Format PRs into a list of dicts for CSV output."""
    changelog_rows = []
    for pr in prs:
        title = pr["title"]
        pr_id = pr["number"]
        url = pr["html_url"]
        labels = [label["name"] for label in pr.get("labels", []) if label["name"].lower() != "plugin: woocommerce"]
        label_str = ", ".join(labels)
        description = fetch_pr_description(pr_id)
        # description = ''
        changelog_rows.append({
            "ID": pr_id,
            "Title": title,
            "Labels": label_str,
            "URL": url,
            "Description": description,
            "Ranking": ""  # Blank for now
        })
    return changelog_rows

def save_changelog(version, content):
    """Save the changelog content to a CSV file."""
    os.makedirs("changelogs", exist_ok=True)
    filename = f"changelogs/{version}.csv"
    
    # If content is a string (from changelog.txt), convert it to a single row
    if isinstance(content, str):
        rows = [{
            "ID": "",
            "Title": f"Changelog for version {version}",
            "Labels": "",
            "URL": "",
            "Description": content,
            "Ranking": ""
        }]
    else:
        rows = content  # content is already a list of dicts from PRs
    
    fieldnames = ["ID", "Title", "Labels", "URL", "Description", "Ranking"]
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Successfully saved changelog to {filename}")
    except Exception as e:
        print(f"Error saving changelog: {e}")
        return False
    return True

if __name__ == "__main__":
    # If no version provided as argument, ask for it
    version = sys.argv[1] if len(sys.argv) > 1 else input("Enter WooCommerce version (e.g. 9.8.0): ")
    # success = fetch_changelog(version)
    success = fetch_prs_from_github(version)
    exit(0 if success else 1)