# WooCommerce Developer Blog Tools

This repository contains a collection of Python scripts to help manage and analyze WooCommerce developer blog content, changelogs, and release information.

## Prerequisites

- Python 3.x
- Required Python packages (install using `pip install -r requirements.txt`):
  - requests
  - pandas
  - python-dotenv

## Environment Setup

1. Create a `.env` file in the root directory with the following content:
```
GITHUB_TOKEN=your_github_token_here
```

## Scripts Overview

### 1. `generate-posts-spreadsheet.py`
Generates a CSV spreadsheet of WordPress posts organized by category and month from the WooCommerce developer blog.

**Usage:**
```bash
python generate-posts-spreadsheet.py
```

**Output:**
- Creates a new file in the `/exports/` directory called `wordpress_posts_by_category.csv` with posts organized by category and month
- Includes proper formatting for Excel compatibility

### 2. `fetch-pr-descriptions.py`
Fetches and adds PR descriptions to changelog files by reading PR references from the changelog.

**Usage:**
```bash
python fetch-pr-descriptions.py <changelog_file>
```

**Features:**
- Reads PR references from changelog files
- Fetches PR descriptions from GitHub
- Updates changelog with PR descriptions
- Handles rate limiting automatically

### 3. `fetch-changelog.py`
Downloads the changelog for a specific WooCommerce version from the WooCommerce GitHub repository.

**Usage:**
```bash
python fetch-changelog.py <version>
# Example: python fetch-changelog.py 9.8
```

**Output:**
- Creates a new file in the `changelogs/` directory named `<version>.txt`
- Downloads changelog content from the WooCommerce trunk branch

### 4. `audit-release-prs.py`
Audits release PRs for WooCommerce releases.

**Usage:**
```bash
python audit-release-prs.py
```

### 5. `fetch-posts.py`
Fetches posts from the WooCommerce developer blog.

**Usage:**
```bash
python fetch-posts.py
```

## Directory Structure

- `changelogs/`: Contains downloaded changelog files
- `release-posts/`: Contains release post content
- `.env`: Environment variables (create this file)


## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create `.env` file with your GitHub token
4. Run the desired script based on your needs

## Notes

- When opening the generated CSV in Excel, you may need to:
  1. Use 'Data' > 'From Text/CSV'
  2. Set the delimiter to comma
  3. Enable 'Treat consecutive delimiters as one'
  4. Set the text qualifier to double quotes
  5. Set the encoding to '65001: Unicode (UTF-8)'

## Contributing

Feel free to submit issues and enhancement requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 