#!/usr/bin/env php
<?php
/**
 * Augment changelog files with PR descriptions from GitHub.
 *
 * Usage: php fetch-pr-descriptions.php <changelog_file>
 *
 * This script reads a changelog file, finds PR references, fetches their
 * descriptions from GitHub, and appends the "Changes proposed" section
 * to the changelog.
 */

require_once __DIR__ . '/includes/functions.php';

// Load environment variables
$env = parse_env_file(__DIR__ . '/.env');
$GITHUB_TOKEN = $env['GITHUB_TOKEN'] ?? '';
$REPO_OWNER = 'woocommerce';
$REPO_NAME = 'woocommerce';

/**
 * Read the changelog file content.
 *
 * @param string $file_path The path to the changelog file
 * @return string The file content
 */
function read_changelog($file_path) {
    if (!file_exists($file_path)) {
        throw new Exception("File not found: {$file_path}");
    }
    return file_get_contents($file_path);
}

/**
 * Find all PR references in the content.
 *
 * @param string $content The changelog content
 * @return array Array of [line, pr_id] tuples
 */
function find_pr_references($content) {
    $pr_pattern = '/\/pull\/(\d+)/';
    $lines = explode("\n", $content);
    $pr_references = [];

    foreach ($lines as $line) {
        if (preg_match($pr_pattern, $line, $matches)) {
            $pr_id = $matches[1];
            $pr_references[] = [$line, $pr_id];
        }
    }

    return $pr_references;
}

/**
 * Fetch PR description from GitHub API.
 *
 * @param string $pr_id The PR ID
 * @return string The full PR body
 */
function fetch_pr_description_body($pr_id) {
    global $GITHUB_TOKEN, $REPO_OWNER, $REPO_NAME;

    if (empty($GITHUB_TOKEN)) {
        throw new Exception("GITHUB_TOKEN environment variable is not set");
    }

    $url = "https://api.github.com/repos/{$REPO_OWNER}/{$REPO_NAME}/pulls/{$pr_id}";
    $response = github_request($url, $GITHUB_TOKEN, true);

    if ($response['http_code'] === 200) {
        $pr_data = json_decode($response['body'], true);
        return $pr_data['body'] ?? '';
    } elseif ($response['http_code'] === 403) {
        echo "Rate limit exceeded. Waiting 60 seconds...\n";
        sleep(60);
        return fetch_pr_description_body($pr_id);
    } else {
        echo "Error fetching PR {$pr_id}: HTTP {$response['http_code']}\n";
        return '';
    }
}

/**
 * Extract the "Changes proposed" section from PR description.
 *
 * @param string $description The full PR description
 * @return string The extracted changes section
 */
function extract_pr_changes_section($description) {
    $pattern = '/Changes proposed in this Pull Request:.*?(?=\n\n|\Z)/s';
    if (preg_match($pattern, $description, $matches)) {
        return trim($matches[0]);
    }
    return '';
}

/**
 * Update the changelog content with PR descriptions.
 *
 * @param string $content The original changelog content
 * @param array $pr_references Array of [line, pr_id] tuples
 * @return string The updated changelog content
 */
function update_changelog($content, $pr_references) {
    $lines = explode("\n", $content);
    $updated_lines = [];

    foreach ($lines as $line) {
        $updated_lines[] = $line;

        foreach ($pr_references as list($ref_line, $pr_id)) {
            if ($line === $ref_line) {
                $description = fetch_pr_description_body($pr_id);
                $changes = extract_pr_changes_section($description);
                if (!empty($changes)) {
                    $updated_lines[] = $changes;
                    $updated_lines[] = ''; // Add blank line for readability
                }
            }
        }
    }

    return implode("\n", $updated_lines);
}

// Main execution
if (php_sapi_name() === 'cli') {
    // Get the changelog file path from command line argument
    if ($argc !== 2) {
        echo "Usage: php fetch-pr-descriptions.php <changelog_file>\n";
        exit(1);
    }

    $changelog_file = $argv[1];

    try {
        // Read the changelog
        $content = read_changelog($changelog_file);

        // Find PR references
        $pr_references = find_pr_references($content);

        if (empty($pr_references)) {
            echo "No PR references found in {$changelog_file}\n";
            exit(0);
        }

        // Update the changelog with PR descriptions
        $updated_content = update_changelog($content, $pr_references);

        // Write the updated content back to the file
        file_put_contents($changelog_file, $updated_content);

        echo "Updated " . count($pr_references) . " PR references in {$changelog_file}\n";

    } catch (Exception $e) {
        echo "Error: " . $e->getMessage() . "\n";
        exit(1);
    }
}
