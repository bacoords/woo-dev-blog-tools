---
name: woocommerce-pr-analyzer
description: Perform deep thematic analysis of WooCommerce release PRs. Use when asked to analyze a release changelog for themes, impact assessment, breaking changes, and release note suggestions. Reads from changelogs/<version>.csv and release-posts/ for context.
---

# WooCommerce PR Analyzer

Perform comprehensive thematic analysis of WooCommerce release PRs to identify major themes, assess impact, and generate release note suggestions.

## Input Sources

### Primary: Changelog CSV

- **Location**: `changelogs/<version>.csv`
- **Format**: CSV with columns:
  - `ID`: PR number
  - `Title`: PR title
  - `Author`: GitHub username of PR author
  - `Labels`: Comma-separated labels (Checkout, Email, WCCOM/Marketplace, etc.)
  - `URL`: GitHub PR URL
  - `Description`: PR description (may be empty)
  - `Ranking`: Optional pre-assigned ranking

### Context: Release Posts

- **Location**: `release-posts/*.txt`
- **Purpose**: Provides context from previous release notes to understand patterns and style

## Workflow

### Step 1: Load Data

1. Read the changelog CSV for the specified version from `changelogs/<version>.csv`
2. Read recent release posts from `release-posts/` directory (up to 3 most recent)
3. If CSV not found, try alternate paths: `<version>.0.csv`, `<version.rstrip('.0')>.csv`

### Step 2: Theme Identification

Group the PRs into themes by analyzing:

- PR titles for common features or areas
- Labels for categorization
- PR descriptions for related functionality
- Patterns indicating work toward the same goal

For each theme, capture:

- **Theme Name**: Descriptive name for the group
- **Overview**: Brief description of what this theme encompasses
- **Related PRs**: List of PR numbers in this theme
- **Contributors**: List of unique GitHub usernames from the Author column for PRs in this theme
- **Impact Level**: HIGH, MEDIUM, or LOW

#### Impact Level Criteria

**HIGH Impact:**

- New major features or capabilities
- Breaking changes or deprecations
- Security-related changes
- Core commerce changes (checkout, payments, cart, orders)
- Changes affecting extension developers (hooks, filters, APIs)

**MEDIUM Impact:**

- Bug fixes for common issues
- Performance improvements
- UX enhancements
- New minor features

**LOW Impact:**

- Internal refactoring
- Test updates
- Documentation changes
- Minor UI tweaks
- i18n/translation updates

### Step 3: Detailed Analysis

For each identified theme, analyze:

**Summary**: Comprehensive overview of what this group of changes accomplishes

**User Impact**: How these changes affect:

- Store owners/administrators
- Customers/shoppers
- Extension developers
- Theme developers

**Technical Details**: Key technical changes or architectural modifications

**Breaking Changes**: Any backwards-incompatible changes that require:

- Code updates
- Database migrations
- Configuration changes

**Dependencies**: Related features or systems affected

**Highlights**: 2-3 most noteworthy PRs in this group and why they matter, including the PR author

### Step 4: Generate Output

Produce a structured analysis report:

```markdown
## WooCommerce <version> PR Analysis

### Theme Overview

1. **[Theme Name]** (Impact: HIGH/MEDIUM/LOW)
   - Overview: [Brief description]
   - Contributors: @username1, @username2, @username3
   - PRs: [List of PR numbers]

2. **[Theme Name]** (Impact: HIGH/MEDIUM/LOW)
   - Overview: [Brief description]
   - Contributors: @username1, @username2
   - PRs: [List of PR numbers]

[Continue for all themes]

---

### Detailed Theme Analysis

#### Theme: [Theme Name]

**Contributors:** @username1, @username2, @username3

**Summary**: [Comprehensive overview]

**User Impact**: [Who is affected and how]

**Technical Details**: [Key technical changes]

**Breaking Changes**: [List any breaking changes or "None"]

**Highlights**:

- PR #[number]: [Why it's noteworthy] (Author: @username)
- PR #[number]: [Why it's noteworthy] (Author: @username)

**Suggested Release Note**:

> [Draft user-friendly release note for this theme]

---

[Repeat for each theme]

---

### Summary Statistics

- Total PRs analyzed: X
- High impact themes: X
- Medium impact themes: X
- Low impact themes: X
- Breaking changes identified: X
```

## Usage

Invoke this skill with a version number:

```
/woocommerce-pr-analyzer 9.9.0
```

The skill will:

1. Load the changelog CSV for version 9.9.0
2. Read recent release posts for context
3. Identify and group PRs into themes
4. Perform detailed analysis of each theme
5. Output the structured analysis report

## Notes

- If PRs have empty descriptions, rely more heavily on titles and labels
- Merge similar themes that emerge from analyzing different parts of the changelog
- Prioritize themes with HIGH impact in the output ordering
- Flag any PRs that seem miscategorized based on content vs. labels
- When in doubt about impact level, consider the perspective of an extension developer
- Extract contributors from the `Author` column and list unique usernames per theme (without PR counts)
- Exclude bot accounts (woocommercebot, github-actions[bot], etc.) from contributor lists when meaningful human contributors exist
