import os
import subprocess
from openai import OpenAI
from pathlib import Path
import re
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
import argparse
import sys

# Load environment variables from .env file
load_dotenv()

# OpenAI API configuration
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
if not os.getenv('OPENAI_API_KEY'):
    raise ValueError("Please set the OPENAI_API_KEY in your .env file")

prompt = """
You are an AI assistant tasked with reviewing a changelog for a software project. Below are the existing release notes from previous versions, which describe past changes and their significance. Using this context, evaluate the provided changelog (list of pull requests) and identify which PRs are "high impact" for inclusion in the next release notes. High-impact PRs include new features, significant bug fixes, or changes that affect users or performance noticeably. Ignore minor updates like documentation changes unless they are critical. Provide your reasoning and a final list of recommended PRs.

### Existing Release Notes
{release_notes_content}

### Changelog
{changelog_content}

### Response Format
- **Recommended PRs**:
  - PR #123: [PR title] - [brief description of why this PR is high impact]
  - PR #456: [PR title] - [brief description of why this PR is high impact]
- **Reasoning**: [overall explanation of the selection]
"""

def clean_html(text):
    """Remove HTML tags and clean up the text."""
    # Remove HTML tags
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text()
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def format_release_note(content):
    """Format a single release note to be more concise."""
    # Extract version and date from the content
    version_match = re.search(r'Version\s+(\d+\.\d+\.?\d*)', content)
    date_match = re.search(r'Date:\s+(\d{4}-\d{2}-\d{2})', content)
    
    version = version_match.group(1) if version_match else "Unknown"
    date = date_match.group(1) if date_match else "Unknown"
    
    # Extract the main content (after the header)
    content_parts = content.split('\n\n', 2)
    if len(content_parts) > 2:
        main_content = content_parts[2]
    else:
        main_content = content
    
    # Clean the content
    cleaned_content = clean_html(main_content)
    
    # Format the release note
    formatted_note = f"Version {version} ({date}):\n{cleaned_content[:500]}..."
    
    return formatted_note

def get_all_release_notes():
    """Get and format all release notes files."""
    release_posts_dir = Path('release-posts')
    if not release_posts_dir.exists():
        return ""
    
    # Get all release note files
    files = list(release_posts_dir.glob('*.txt'))
    if not files:
        return ""
    
    # Sort files by date (newest first)
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    # Process each file
    formatted_notes = []
    for file in files:
        content = file.read_text()
        formatted_note = format_release_note(content)
        formatted_notes.append(formatted_note)
    
    # Join all notes with separators
    return "\n\n---\n\n".join(formatted_notes)

def run_script(script_name, *args):
    """Run a Python script and return True if successful."""
    try:
        subprocess.run([sys.executable, script_name, *args], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
        return False

def get_changelog_content(version):
    """Get the content of the changelog for the specified version."""
    changelog_path = Path(f'changelogs/{version}.txt')
    if not changelog_path.exists():
        return ""
    return changelog_path.read_text()

def analyze_with_openai(release_notes, changelog):
    """Send the content to OpenAI for analysis."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a technical writer reviewing changelogs for WooCommerce releases."},
                {"role": "user", "content": prompt.format(
                    release_notes_content=release_notes,
                    changelog_content=changelog
                )}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Audit WooCommerce release PRs')
    parser.add_argument('--fetch-posts', action='store_true', 
                       help='Fetch release posts')
    parser.add_argument('--fetch-changelog', action='store_true',
                       help='Fetch changelog')
    parser.add_argument('--version', type=str,
                       help='WooCommerce version (e.g. 9.8)')
    args = parser.parse_args()

    # Step 1: Run fetch-posts.py (if requested)
    if args.fetch_posts:
        print("Fetching release posts...")
        if not run_script('fetch-posts.py'):
            return
    else:
        print("Skipping fetch-posts.py")

    # Step 2: Get version input if not provided as argument
    version = args.version
    if not version:
        version = input("Enter WooCommerce version (e.g. 9.8): ")

    # Step 3: Run fetch-changelog.py with the version (if requested)
    if args.fetch_changelog:
        print(f"Fetching changelog for version {version}...")
        if not run_script('fetch-changelog.py', version):
            return
    else:
        print("Skipping fetch-changelog.py")

    # Step 4: Get content and analyze with OpenAI
    print("Analyzing content with OpenAI...")
    release_notes = get_all_release_notes()
    changelog = get_changelog_content(version)

    if not release_notes or not changelog:
        print("Error: Could not find required content files")
        return

    analysis = analyze_with_openai(release_notes, changelog)
    if analysis:
        print("\nAnalysis Results:")
        print(analysis)
    else:
        print("Failed to get analysis from OpenAI")

if __name__ == "__main__":
    main()





