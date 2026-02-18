---
name: woo-data-fetch
description: Fetch WooCommerce release data and generate reports. Runs the orchestrator to fetch changelog and release posts, and optionally generates a posts spreadsheet. Use when asked to fetch release data, prepare for release analysis, or generate content reports.
---

# WooCommerce Data Fetch

Fetch WooCommerce release data from GitHub and the developer blog, and generate summary reports.

## What This Skill Does

This skill automates the data fetching workflow by running:
1. **Changelog fetch** - Downloads PR data from GitHub for a specific WooCommerce version
2. **Release posts fetch** - Downloads recent release posts from developer.woocommerce.com
3. **Posts spreadsheet** - Generates a CSV report of blog posts organized by category and month

## Usage

### Fetch all data for a release version
```
/woo-data-fetch 9.9.0
```
This will:
- Fetch the changelog for version 9.9.0 from GitHub
- Fetch recent release posts from the developer blog
- Generate the posts spreadsheet

### Fetch with specific options
```
/woo-data-fetch 9.9.0 --no-spreadsheet
```
Skip the spreadsheet generation.

```
/woo-data-fetch --posts-only
```
Only fetch release posts and generate the spreadsheet (no changelog).

## Workflow

### Step 1: Parse Arguments

Extract from the user's input:
- **version**: The WooCommerce version number (e.g., 9.9.0)
- **options**: Any flags like `--no-spreadsheet` or `--posts-only`

### Step 2: Run Data Fetch Scripts

Execute the PHP scripts in order:

#### If version is provided (default behavior):
```bash
php audit-release-prs.php --fetch-changelog --fetch-posts --version=<version>
```

#### If --posts-only flag:
```bash
php fetch-posts.php
```

### Step 3: Generate Posts Spreadsheet

Unless `--no-spreadsheet` is specified:
```bash
php generate-posts-spreadsheet.php
```

### Step 4: Verify and Report

After running the scripts, verify the outputs exist and report:

1. **Check changelog**: Look for `changelogs/<version>.csv`
2. **Check release posts**: Verify `release-posts/` has `.txt` files
3. **Check spreadsheet**: Verify `exports/wordpress_posts_by_category.csv` exists

### Step 5: Provide Next Steps

After successful data fetch, inform the user about analysis options:

```markdown
## Data Fetch Complete

### Files Generated
- Changelog: `changelogs/<version>.csv`
- Release posts: `release-posts/` (X files)
- Spreadsheet: `exports/wordpress_posts_by_category.csv`

### Next Steps - Analyze with Claude

For full thematic analysis:
```
/woocommerce-pr-analyzer <version>
```

For quick relevance scoring:
```
/woocommerce-release-comms <version>
```
```

## Error Handling

If any script fails:
1. Report which script failed
2. Check if `.env` file exists with `GITHUB_TOKEN`
3. Suggest running the script manually with verbose output
4. Provide troubleshooting steps

Common issues:
- **Missing GITHUB_TOKEN**: Remind user to set up `.env` file
- **Rate limit**: GitHub API rate limit hit - wait and retry
- **Network errors**: Check internet connection

## Output Locations

| Data | Location |
|------|----------|
| Changelog CSV | `changelogs/<version>.csv` |
| Release posts | `release-posts/*.txt` |
| Posts spreadsheet | `exports/wordpress_posts_by_category.csv` |

## Examples

### Full data fetch for release 9.9.0
```
/woo-data-fetch 9.9.0
```

### Just update release posts and spreadsheet
```
/woo-data-fetch --posts-only
```

### Fetch changelog only (no spreadsheet)
```
/woo-data-fetch 9.9.0 --no-spreadsheet
```

## Notes

- The GITHUB_TOKEN environment variable must be set in `.env` for changelog fetching
- Changelog fetch may take a few minutes for releases with many PRs
- The posts spreadsheet covers the last 12 months of blog posts
- Rate limiting is handled automatically with a 60-second retry
