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
import json
import logging

# Load environment variables from .env file
load_dotenv()

# OpenAI API configuration
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
if not os.getenv('OPENAI_API_KEY'):
    raise ValueError("Please set the OPENAI_API_KEY in your .env file")

detailed_analysis_prompt = """
You are an AI assistant performing a detailed analysis of a specific theme of changes for a software release. Below is a group of related PRs that work together towards a common goal or feature. Analyze their collective impact and provide a comprehensive summary.

### Theme
{theme_name}

### Related Pull Requests
{theme_prs}

### Previous Release Notes (For Context)
{release_notes_content}

### Response Format
THEME ANALYSIS:
- **Summary**: [Comprehensive overview of what this group of changes accomplishes]
- **User Impact**: [How these changes affect end users or developers]
- **Technical Details**: [Key technical changes or architectural modifications]
- **Breaking Changes**: [Any backwards-incompatible changes]
- **Dependencies**: [Related features or systems affected]
- **Highlights**: [2-3 most noteworthy PRs in this group and why]

SUGGESTED RELEASE NOTE:
[Draft a concise, user-friendly release note section for this theme]
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
    # Extract version from various possible formats in the content
    version_patterns = [
        r'Version\s+(\d+\.\d+\.?\d*)',
        r'WooCommerce\s+(\d+\.\d+\.?\d*)',
        r'woocommerce-(\d+\.\d+\.?\d*)',
    ]
    
    version = "Unknown"
    for pattern in version_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            version = match.group(1)
            break
    
    # Extract date from filename or content
    date_match = re.search(r'Date:\s+(\d{4}-\d{2}-\d{2})', content)
    date = date_match.group(1) if date_match else "Unknown"
    
    # Extract the main content (after the header)
    content_parts = content.split('\n\n', 2)
    if len(content_parts) > 2:
        main_content = content_parts[2]
    else:
        main_content = content
    
    # Clean the content
    cleaned_content = clean_html(main_content)
    
    # Format the release note more concisely
    formatted_note = f"Version {version} ({date}):\n{cleaned_content[:300]}..."
    
    return formatted_note, version

def get_all_release_notes(current_version=None, max_versions=3):
    """Get and format recent release notes files."""
    release_posts_dir = Path('release-posts')
    if not release_posts_dir.exists():
        print(f"Error: Release posts directory not found at {release_posts_dir}")
        print("Please run with --fetch-posts flag to fetch release posts first")
        return None
    
    # Get all release note files
    files = list(release_posts_dir.glob('*.txt'))
    if not files:
        print("Error: No release note files found in release-posts directory")
        print("Please run with --fetch-posts flag to fetch release posts first")
        return None
    
    # Sort files by version number if possible
    notes_with_versions = []
    for file in files:
        try:
            content = file.read_text()
            formatted_note, version = format_release_note(content)
            if version != "Unknown":
                # Normalize version number (remove trailing .0 if present)
                major_minor = '.'.join(version.split('.')[:2])  # Get major.minor version
                notes_with_versions.append((major_minor, formatted_note))
        except Exception as e:
            print(f"Warning: Could not process file {file}: {e}")
            continue
    
    if not notes_with_versions:
        print("Error: Could not parse version numbers from release notes")
        print("Files checked:")
        for file in files[:5]:  # Show first 5 files
            print(f"- {file}")
        return None
    
    # Sort by version number (newest first)
    notes_with_versions.sort(key=lambda x: [int(n) for n in x[0].split('.')], reverse=True)
    
    # If current_version is provided, only include notes from previous versions
    if current_version:
        current_major_minor = '.'.join(current_version.split('.')[:2])
        notes_with_versions = [
            (v, n) for v, n in notes_with_versions 
            if v < current_major_minor
        ]
    
    # Take only the most recent versions
    selected_notes = [note for _, note in notes_with_versions[:max_versions]]
    
    if not selected_notes:
        print(f"Warning: No release notes found for versions before {current_version}")
        # Fall back to most recent notes if we can't find older ones
        selected_notes = [note for _, note in notes_with_versions[:max_versions]]
    
    # Join all notes with separators
    return "\n\n---\n\n".join(selected_notes)

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
    # Try both with and without .0 suffix
    possible_paths = [
        Path(f'changelogs/{version}.txt'),
        Path(f'changelogs/{version}.0.txt'),
        Path(f'changelogs/{version.rstrip(".0")}.txt')
    ]
    
    for path in possible_paths:
        if path.exists():
            return path.read_text()
    
    print(f"Error: Changelog file not found. Tried:")
    for path in possible_paths:
        print(f"- {path}")
    print("Please run with --fetch-changelog flag to fetch the changelog first")
    return None

def chunk_changelog(changelog, chunk_size=4000):
    """Split changelog into smaller chunks if it's too large."""
    # Split by PRs (assumed to be separated by newlines)
    prs = changelog.split('\n')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for pr in prs:
        pr_size = len(pr)
        if current_size + pr_size > chunk_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_size = 0
        current_chunk.append(pr)
        current_size += pr_size
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

def setup_logging(version):
    """Set up logging to both file and console."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f'audit_{version}_{timestamp}.log'
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return log_file

def log_openai_interaction(prompt, response, stage):
    """Log OpenAI interaction details to a JSON file."""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    interaction_file = log_dir / f'openai_interactions_{timestamp}.json'
    
    interaction = {
        'timestamp': datetime.now().isoformat(),
        'stage': stage,
        'prompt': prompt,
        'response': response
    }
    
    # Load existing interactions if file exists
    existing_interactions = []
    if interaction_file.exists():
        try:
            with open(interaction_file, 'r') as f:
                existing_interactions = json.load(f)
        except json.JSONDecodeError:
            existing_interactions = []
    
    # Append new interaction
    existing_interactions.append(interaction)
    
    # Save updated interactions
    with open(interaction_file, 'w') as f:
        json.dump(existing_interactions, f, indent=2)

def analyze_with_openai(release_notes, changelog, version):
    """Send the content to OpenAI for analysis in two stages."""
    try:
        # Get only recent release notes
        recent_notes = get_all_release_notes(version, max_versions=3)
        logging.info(f"Retrieved {len(recent_notes.split('---'))} recent release notes")
        
        # Split changelog into chunks if needed
        changelog_chunks = chunk_changelog(changelog)
        logging.info(f"Split changelog into {len(changelog_chunks)} chunks")
        all_themes = []
        
        # Stage 1: Theme Identification (process each chunk)
        logging.info("Starting theme identification...")
        for i, chunk in enumerate(changelog_chunks, 1):
            if len(changelog_chunks) > 1:
                logging.info(f"Processing chunk {i} of {len(changelog_chunks)}...")
            
            prompt = theme_identification_prompt.format(
                release_notes_content=recent_notes,
                changelog_content=chunk
            )
            
            themes_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a technical writer reviewing changelogs for WooCommerce releases."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_content = themes_response.choices[0].message.content
            log_openai_interaction(prompt, response_content, f"theme_identification_chunk_{i}")
            
            chunk_themes = parse_themes(response_content)
            logging.info(f"Found {len(chunk_themes)} themes in chunk {i}")
            all_themes.extend(chunk_themes)
        
        # Merge similar themes if processing multiple chunks
        if len(changelog_chunks) > 1:
            logging.info("Merging similar themes...")
            all_themes = merge_similar_themes(all_themes)
            logging.info(f"After merging: {len(all_themes)} unique themes")
        
        # Stage 2: Detailed Analysis for each theme
        logging.info("Starting detailed theme analysis...")
        detailed_analyses = []
        for i, theme in enumerate(all_themes, 1):
            logging.info(f"Analyzing theme {i}/{len(all_themes)}: {theme['name']}")
            
            prompt = detailed_analysis_prompt.format(
                theme_name=theme['name'],
                theme_prs=theme['prs'],
                release_notes_content=recent_notes
            )
            
            detailed_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a technical writer reviewing changelogs for WooCommerce releases."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_content = detailed_response.choices[0].message.content
            log_openai_interaction(prompt, response_content, f"detailed_analysis_theme_{i}")
            detailed_analyses.append(response_content)

        # Combine all analyses
        separator = '\n' + '=' * 80 + '\n'
        final_output = (
            "THEME OVERVIEW:\n"
            f"{format_themes_overview(all_themes)}\n\n"
            "DETAILED ANALYSES:\n"
            f"{'=' * 80}\n"
            f"{separator.join(detailed_analyses)}"
        )
        
        # Log the final output
        logging.info("Analysis complete. Saving final output...")
        log_openai_interaction("Final Analysis", final_output, "final_output")
        
        return final_output
    except Exception as e:
        logging.error(f"Error in OpenAI analysis: {str(e)}", exc_info=True)
        return None

def parse_themes(themes_analysis):
    """Parse the themes from the OpenAI response."""
    themes = []
    current_theme = None
    
    # Simple parsing logic - can be enhanced based on actual response format
    for line in themes_analysis.split('\n'):
        if line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
            if current_theme:
                themes.append(current_theme)
            theme_name = line.split('.', 1)[1].strip()
            current_theme = {'name': theme_name, 'prs': ''}
        elif current_theme and 'Related PRs:' in line:
            current_theme['prs'] = line.split('Related PRs:', 1)[1].strip()
    
    if current_theme:
        themes.append(current_theme)
    
    return themes

def merge_similar_themes(themes):
    """Merge themes that appear to be related based on name similarity."""
    merged = []
    used = set()
    
    for i, theme1 in enumerate(themes):
        if i in used:
            continue
            
        similar_themes = [theme1]
        for j, theme2 in enumerate(themes[i+1:], i+1):
            if j in used:
                continue
                
            # Simple similarity check - can be enhanced
            if similar_words(theme1['name'], theme2['name']):
                similar_themes.append(theme2)
                used.add(j)
        
        if similar_themes:
            merged.append({
                'name': similar_themes[0]['name'],
                'prs': '; '.join(t['prs'] for t in similar_themes)
            })
        used.add(i)
    
    return merged

def similar_words(str1, str2):
    """Simple check if strings share significant words."""
    words1 = set(str1.lower().split())
    words2 = set(str2.lower().split())
    return len(words1.intersection(words2)) >= 2

def format_themes_overview(themes):
    """Format themes into a readable overview."""
    return '\n'.join(f"{i+1}. {theme['name']}\n   PRs: {theme['prs']}" 
                    for i, theme in enumerate(themes))

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

    # Get version input if not provided as argument
    version = args.version
    if not version:
        version = input("Enter WooCommerce version (e.g. 9.8): ")

    # Set up logging
    log_file = setup_logging(version)
    logging.info(f"Starting analysis for WooCommerce version {version}")
    logging.info(f"Log file: {log_file}")

    # Step 1: Run fetch-posts.py (if requested)
    if args.fetch_posts:
        logging.info("Fetching release posts...")
        if not run_script('fetch-posts.py'):
            logging.error("Failed to fetch release posts")
            return
    else:
        logging.info("Skipping fetch-posts.py")

    # Step 2: Run fetch-changelog.py with the version (if requested)
    if args.fetch_changelog:
        logging.info(f"Fetching changelog for version {version}...")
        if not run_script('fetch-changelog.py', version):
            logging.error("Failed to fetch changelog")
            return
    else:
        logging.info("Skipping fetch-changelog.py")

    # Step 3: Get content and analyze with OpenAI
    logging.info("Starting content analysis...")
    release_notes = get_all_release_notes(version)
    changelog = get_changelog_content(version)

    if not release_notes or not changelog:
        logging.error("Required content files not found")
        logging.info("\nPlease ensure both release posts and changelog are available:")
        logging.info("1. Run with --fetch-posts to get release posts")
        logging.info("2. Run with --fetch-changelog to get the changelog")
        logging.info(f"3. Check that the files exist in release-posts/ and changelogs/{version}.txt")
        return

    analysis = analyze_with_openai(release_notes, changelog, version)
    if analysis:
        logging.info("Analysis complete. Results:")
        print("\nAnalysis Results:")
        print(analysis)
    else:
        logging.error("Failed to get analysis from OpenAI")

if __name__ == "__main__":
    main()





