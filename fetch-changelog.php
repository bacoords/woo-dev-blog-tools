#!/usr/bin/env php
<?php
/**
 * Fetch WooCommerce changelog from GitHub.
 *
 * Usage: php fetch-changelog.php <version>
 *
 * This script fetches the changelog for a specific WooCommerce version,
 * either from the trunk changelog.txt or by querying the GitHub API
 * for PRs in the corresponding milestone.
 */

require_once __DIR__ . '/includes/functions.php';

// Load environment variables
$env = parse_env_file(__DIR__ . '/.env');
$GITHUB_TOKEN = $env['GITHUB_TOKEN'] ?? '';
$REPO_OWNER = 'woocommerce';
$REPO_NAME = 'woocommerce';

/**
 * Fetch changelog from trunk changelog.txt
 *
 * @param string $version The version to fetch
 * @return bool True on success, false on failure
 */
function fetch_changelog($version) {
    $changelog_url = 'https://raw.githubusercontent.com/woocommerce/woocommerce/refs/heads/trunk/changelog.txt';

    $ch = curl_init($changelog_url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_HTTPHEADER => ['User-Agent: WooDevTools']
    ]);

    $content = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($http_code !== 200 || empty($content)) {
        echo "Error fetching changelog from trunk\n";
        return fetch_prs_from_github($version);
    }

    // Find the specific version section
    $version_marker = "= {$version} ";
    if (strpos($content, $version_marker) === false) {
        echo "Changelog section for version {$version} not found. Attempting to generate from GitHub API...\n";
        return fetch_prs_from_github($version);
    }

    // Split at the version marker and get the content up to the next version
    $parts = explode($version_marker, $content);
    if (count($parts) < 2) {
        echo "Error: Could not find changelog section for version {$version}\n";
        return false;
    }

    // Get the content up to the next version marker
    $changelog_parts = explode('= ', $parts[1]);
    $changelog_content = trim($changelog_parts[0]);

    // Save the changelog to a file
    save_changelog($version, $changelog_content);
    return true;
}

/**
 * Fetch PRs from GitHub API for the specified milestone.
 *
 * @param string $version The version to fetch
 * @return bool True on success, false on failure
 */
function fetch_prs_from_github($version) {
    global $GITHUB_TOKEN, $REPO_OWNER, $REPO_NAME;

    if (empty($GITHUB_TOKEN)) {
        echo "Error: GITHUB_TOKEN environment variable is not set\n";
        return false;
    }

    // First verify the milestone exists
    $milestone_url = "https://api.github.com/repos/{$REPO_OWNER}/{$REPO_NAME}/milestones";

    $response = github_request($milestone_url, $GITHUB_TOKEN, true);
    if ($response['http_code'] === 403) {
        echo "Error: GitHub API rate limit exceeded. Please try again later.\n";
        return false;
    }

    $milestones = json_decode($response['body'], true);
    if (!is_array($milestones)) {
        echo "Error: Could not fetch milestones\n";
        return false;
    }

    // Find the milestone that matches our version
    $milestone_number = null;
    foreach ($milestones as $milestone) {
        if ($milestone['title'] === $version) {
            $milestone_number = $milestone['number'];
            echo "Found milestone {$version} with number {$milestone_number}\n";
            break;
        }
    }

    if ($milestone_number === null) {
        echo "Warning: Could not find milestone for version {$version}\n";
        echo "Available milestones:\n";
        foreach ($milestones as $m) {
            echo "- {$m['title']}\n";
        }
        return false;
    }

    // Now fetch PRs with the correct milestone number
    $url = "https://api.github.com/repos/{$REPO_OWNER}/{$REPO_NAME}/issues";
    $params = [
        'state' => 'closed',
        'milestone' => (string)$milestone_number,
        'per_page' => 100
    ];

    $all_prs = [];
    $next_url = $url . '?' . http_build_query($params);
    $page_count = 0;

    while ($next_url) {
        $page_count++;
        echo "Fetching PRs from page {$page_count}...\n";

        $response = github_request($next_url, $GITHUB_TOKEN, true);
        $issues = json_decode($response['body'], true);

        if (!is_array($issues) || empty($issues)) {
            echo "No more PRs found, stopping pagination.\n";
            break;
        }

        // Filter to only include PRs (issues with pull_request field)
        $prs = array_filter($issues, function($issue) {
            return isset($issue['pull_request']);
        });

        echo "Found " . count($prs) . " PRs on this page\n";
        $all_prs = array_merge($all_prs, $prs);

        // Get the next page URL from the Link header
        $next_url = parse_next_page_url($response['headers']['link'] ?? '');

        if (!$next_url) {
            echo "No more pages available\n";
            break;
        }
    }

    echo "Total PRs found: " . count($all_prs) . "\n";

    if (empty($all_prs)) {
        echo "No PRs found for milestone {$version}.\n";
        return false;
    }

    // Format PRs into changelog format
    $changelog_rows = format_prs_as_changelog($all_prs);
    save_changelog($version, $changelog_rows);
    return true;
}

/**
 * Fetch PR description from GitHub API.
 *
 * @param int $pr_id The PR ID
 * @return string The extracted changes section
 */
function fetch_pr_description($pr_id) {
    global $GITHUB_TOKEN, $REPO_OWNER, $REPO_NAME;

    if (empty($GITHUB_TOKEN)) {
        echo "Error: GITHUB_TOKEN environment variable is not set\n";
        return '';
    }

    $url = "https://api.github.com/repos/{$REPO_OWNER}/{$REPO_NAME}/pulls/{$pr_id}";
    $response = github_request($url, $GITHUB_TOKEN, true);

    if ($response['http_code'] === 200) {
        $pr_data = json_decode($response['body'], true);
        return extract_changes_section($pr_data['body'] ?? '');
    } elseif ($response['http_code'] === 403) {
        // Rate limit handled inside github_request, but just in case
        echo "Rate limit exceeded. Waiting 60 seconds...\n";
        sleep(60);
        return fetch_pr_description($pr_id);
    } else {
        echo "Error fetching PR {$pr_id}: HTTP {$response['http_code']}\n";
        return '';
    }
}

/**
 * Format PRs into a list of associative arrays for CSV output.
 *
 * @param array $prs The PRs to format
 * @return array The formatted changelog rows
 */
function format_prs_as_changelog($prs) {
    $changelog_rows = [];

    foreach ($prs as $pr) {
        $title = $pr['title'];
        $pr_id = $pr['number'];
        $url = $pr['html_url'];
        $author = $pr['user']['login'] ?? '';

        // Get labels, excluding "plugin: woocommerce"
        $labels = array_filter($pr['labels'] ?? [], function($label) {
            return strtolower($label['name']) !== 'plugin: woocommerce';
        });
        $label_names = array_map(function($label) {
            return $label['name'];
        }, $labels);
        $label_str = implode(', ', $label_names);

        // Fetch PR description
        $description = fetch_pr_description($pr_id);

        $changelog_rows[] = [
            'ID' => $pr_id,
            'Title' => $title,
            'Author' => $author,
            'Labels' => $label_str,
            'URL' => $url,
            'Description' => $description,
            'Ranking' => '' // Blank for now
        ];
    }

    return $changelog_rows;
}

/**
 * Save the changelog content to a CSV file.
 *
 * @param string $version The version
 * @param mixed $content The content (string or array of rows)
 * @return bool True on success, false on failure
 */
function save_changelog($version, $content) {
    ensure_directory('changelogs');
    $filename = "changelogs/{$version}.csv";

    // If content is a string (from changelog.txt), convert it to a single row
    if (is_string($content)) {
        $rows = [[
            'ID' => '',
            'Title' => "Changelog for version {$version}",
            'Author' => '',
            'Labels' => '',
            'URL' => '',
            'Description' => $content,
            'Ranking' => ''
        ]];
    } else {
        $rows = $content; // content is already a list of dicts from PRs
    }

    $headers = ['ID', 'Title', 'Author', 'Labels', 'URL', 'Description', 'Ranking'];

    if (write_csv_with_bom($filename, $headers, $rows)) {
        echo "Successfully saved changelog to {$filename}\n";
        return true;
    } else {
        echo "Error saving changelog\n";
        return false;
    }
}

// Main execution
if (php_sapi_name() === 'cli') {
    // Get version from argument or prompt
    $version = $argv[1] ?? null;

    if (!$version) {
        echo "Enter WooCommerce version (e.g. 9.8.0): ";
        $version = trim(fgets(STDIN));
    }

    if (empty($version)) {
        echo "Error: Version is required\n";
        echo "Usage: php fetch-changelog.php <version>\n";
        exit(1);
    }

    // Use fetch_prs_from_github directly like the Python script does
    $success = fetch_prs_from_github($version);
    exit($success ? 0 : 1);
}
