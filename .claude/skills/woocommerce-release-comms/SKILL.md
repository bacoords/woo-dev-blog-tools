---
name: woocommerce-release-comms
description: Analyze WooCommerce changelog files to identify and rank changes most relevant to the developer community. Use when asked to review, summarize, or prioritize WooCommerce changelog entries, find notable changes, or generate release highlights from the ../woocommerce/plugins/woocommerce/changelog/ directory.
---

# WooCommerce Changelog Analyzer

Analyze changelog files to surface changes most relevant to WooCommerce developers.

## Input Sources

This skill supports two input sources:

### Source 1: Local CSV Files (Preferred for Release Analysis)
- **Location**: `changelogs/<version>.csv`
- **Format**: CSV with columns: `Number`, `Title`, `Labels`, `URL`, `Description`, `Ranking`
- **Usage**: When a version number is provided (e.g., `/woocommerce-release-comms 9.9.0`)

### Source 2: WooCommerce Repository Changelog Directory
- **Location**: `../woocommerce/plugins/woocommerce/changelog/`
- **Format**: Individual changelog entry files
- **Usage**: When analyzing the raw WooCommerce changelog directory

## Workflow

### For Local CSV Files (changelogs/<version>.csv)

1. **Read CSV file**: Parse `changelogs/<version>.csv`
2. **Extract PR information**: Number, Title, Labels, URL, Description
3. **Categorize and score**: Apply relevance scoring based on title, labels, and description
4. **Output ranked summary**: Present changes sorted by developer relevance

### For WooCommerce Repository Changelog

1. **Scan changelog directory**: List all files in `../woocommerce/plugins/woocommerce/changelog/`
2. **Read each changelog file**: Parse the change description, type, and metadata
3. **Categorize and score**: Assign each change to a category and relevance score
4. **Output ranked summary**: Present changes sorted by developer relevance

## CSV Parsing

When reading from local CSV files:
- Parse the CSV header to identify columns
- Extract PR metadata from each row
- Use Labels column for categorization hints
- Use Title and Description for keyword matching

## Changelog File Format (Repository Source)

Each file in the WooCommerce repository changelog typically contains:
- Change type (fix, add, update, tweak, dev, etc.)
- Brief description of the change
- Related issue/PR references, or the PR might be in the filename

## Relevance Categories (High to Low Priority)

### Level 1 - High Impact
- **New Features**: New functionality, APIs, hooks, or capabilities
- **Breaking Changes**: Deprecations, removed features, API changes
- **Security Fixes**: Any security-related patches

### Level 2 - Developer Interest
- **Developer Tools**: New hooks, filters, REST API changes, CLI updates
- **Performance**: Optimizations, caching improvements, query efficiency
- **Major Bug Fixes**: Fixes for data loss, checkout failures, payment issues

### Level 3 - General Updates
- **Minor Bug Fixes**: UI glitches, edge cases, non-critical fixes
- **Tweaks**: Small improvements, UX polish
- **Internal**: Code refactoring, test updates, documentation

## Scoring Heuristics

Increase relevance score when changelog mentions:
- `hook`, `filter`, `action`, `API`, `REST`, `endpoint` → Developer tooling
- `security`, `vulnerability`, `XSS`, `CSRF`, `injection` → Security (highest priority)
- `deprecated`, `removed`, `breaking`, `migration` → Breaking changes
- `performance`, `speed`, `optimize`, `cache` → Performance
- `new`, `add`, `introduce`, `feature` → New features
- `checkout`, `payment`, `cart`, `order` → Core commerce (high impact)

Decrease relevance score for:
- `typo`, `spacing`, `whitespace`, `css` → Low impact
- `test`, `phpunit`, `e2e` → Internal only
- `i18n`, `translation` → Localization (unless adding new language)

## Output Format

```markdown
## WooCommerce Changelog Analysis

### 🔴 High Impact Changes
[List changes with brief explanation of why they matter]

### 🟡 Developer-Relevant Changes  
[List changes relevant to extension developers]

### 🟢 Other Notable Changes
[Brief summary of remaining changes worth mentioning]

### Summary Statistics
- Total changes analyzed: X
- High impact: X
- Developer-relevant: X
- Minor/Internal: X
```

## Usage

### Analyze a specific release version (from local CSV)
```
/woocommerce-release-comms 9.9.0
```
This reads from `changelogs/9.9.0.csv` and produces a ranked summary.

### Analyze WooCommerce repository changelog
```
/woocommerce-release-comms
```
This reads from `../woocommerce/plugins/woocommerce/changelog/` directory.

## Usage Notes

- When analyzing a large number of files, process in batches and aggregate results
- Include file names or PR numbers in output for traceability
- Flag any changes that seem miscategorized based on content vs. stated type
- If changelog format varies, adapt parsing accordingly
- For quick relevance scoring, this skill is faster than the full thematic analysis provided by `/woocommerce-pr-analyzer`