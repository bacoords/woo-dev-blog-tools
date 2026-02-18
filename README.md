# WooCommerce Developer Blog Tools

This repository contains a collection of PHP scripts and Claude skills to help manage and analyze WooCommerce developer blog content, changelogs, and release information.

## Prerequisites

- PHP 8.1+ with cURL extension
- Claude Code CLI (for analysis skills)

## Environment Setup

1. Create a `.env` file in the root directory with the following content:

```txt
GITHUB_TOKEN=your_github_token_here
```

## Quick Start: Release Analysis

The recommended workflow for analyzing WooCommerce releases:

### 1. Fetch Data (PHP)

```bash
# Fetch changelog for a specific version
php fetch-changelog.php 9.9.0

# Fetch release posts for context
php fetch-posts.php
```

Or use the orchestrator script:

```bash
php audit-release-prs.php --fetch-changelog --fetch-posts --version=9.9.0
```

### 2. Analyze (Claude Skills)

For full thematic analysis with impact assessment and release note suggestions:
```
/woocommerce-pr-analyzer 9.9.0
```

For quick relevance scoring:
```
/woocommerce-release-comms 9.9.0
```

## Scripts Overview

### Data Fetching Scripts

#### `fetch-changelog.php`

Downloads the changelog for a specific WooCommerce version from the WooCommerce GitHub repository.

**Usage:**

```bash
php fetch-changelog.php <version>
# Example: php fetch-changelog.php 9.9.0
```

**Output:**

- Creates files in the `changelogs/` directory (`<version>.csv`)
- Downloads changelog content from the WooCommerce trunk branch
- Falls back to generating changelog from GitHub PRs if trunk version not found

#### `fetch-pr-descriptions.php`

Fetches and adds PR descriptions to changelog files by reading PR references from the changelog.

**Usage:**

```bash
php fetch-pr-descriptions.php <changelog_file>
```

#### `fetch-posts.php`

Fetches posts from the WooCommerce developer blog.

**Usage:**

```bash
php fetch-posts.php
```

#### `generate-posts-spreadsheet.php`

Generates a CSV spreadsheet of WordPress posts organized by category and month.

**Usage:**

```bash
php generate-posts-spreadsheet.php
```

**Output:**

- Creates `/exports/wordpress_posts_by_category.csv`

### Orchestrator Script

#### `audit-release-prs.php`

Coordinates data fetching and provides instructions for Claude analysis.

**Usage:**

```bash
# Fetch all data for a version
php audit-release-prs.php --fetch-changelog --fetch-posts --version=9.9.0

# Check if data files exist
php audit-release-prs.php --check --version=9.9.0

# Show help
php audit-release-prs.php --help
```

## Claude Skills

### `/woocommerce-pr-analyzer`

Performs deep thematic analysis of WooCommerce release PRs:
- Groups PRs into themes
- Assesses impact (HIGH/MEDIUM/LOW)
- Identifies breaking changes
- Generates release note suggestions

**Usage:**
```
/woocommerce-pr-analyzer 9.9.0
```

### `/woocommerce-release-comms`

Quick relevance scoring for changelog entries:
- Ranks changes by developer relevance
- Categorizes by impact level
- Provides summary statistics

**Usage:**
```
/woocommerce-release-comms 9.9.0
```

## Directory Structure

```
.
├── includes/            # Shared PHP functions
│   └── functions.php
├── changelogs/          # Downloaded changelog files (CSV)
├── release-posts/       # Release post content from developer blog
├── exports/             # Generated CSV exports
├── .claude/
│   └── skills/          # Claude skill definitions
│       ├── woocommerce-pr-analyzer/
│       └── woocommerce-release-comms/
└── .env                 # Environment variables (create this)
```

## Notes

- When opening generated CSVs in Excel, you may need to set UTF-8 encoding
- The `GITHUB_TOKEN` is required for fetching changelog data from GitHub
- Claude skills require Claude Code CLI to be installed and configured

## Contributing

Feel free to submit issues and enhancement requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
