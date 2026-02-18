#!/usr/bin/env php
<?php
/**
 * Fetch WooCommerce release data for analysis.
 *
 * This script fetches changelog and release post data, preparing it for
 * analysis using Claude skills:
 * - /woocommerce-pr-analyzer <version> - Full thematic analysis
 * - /woocommerce-release-comms <version> - Quick relevance scoring
 *
 * Usage:
 *   php audit-release-prs.php --fetch-changelog --fetch-posts --version=9.9.0
 *   php audit-release-prs.php --check --version=9.9.0
 */

require_once __DIR__ . '/includes/functions.php';

/**
 * Run a PHP script and return true if successful.
 *
 * @param string $script_name The script filename
 * @param array $args Arguments to pass
 * @return bool True if successful
 */
function run_script($script_name, $args = []) {
    $script_path = __DIR__ . '/' . $script_name;

    if (!file_exists($script_path)) {
        echo "Error: Script not found: {$script_name}\n";
        return false;
    }

    $command = 'php ' . escapeshellarg($script_path);
    foreach ($args as $arg) {
        $command .= ' ' . escapeshellarg($arg);
    }

    $output = [];
    $return_var = 0;
    exec($command, $output, $return_var);

    // Print output
    foreach ($output as $line) {
        echo $line . "\n";
    }

    return $return_var === 0;
}

/**
 * Check if changelog file exists for the specified version.
 *
 * @param string $version The version to check
 * @return string|null The path if found, null otherwise
 */
function check_changelog_exists($version) {
    $possible_paths = [
        "changelogs/{$version}.csv",
        "changelogs/{$version}.0.csv",
        "changelogs/" . rtrim($version, '.0') . ".csv",
        "changelogs/{$version}.txt",
        "changelogs/{$version}.0.txt",
        "changelogs/" . rtrim($version, '.0') . ".txt",
    ];

    foreach ($possible_paths as $path) {
        if (file_exists($path)) {
            return $path;
        }
    }

    return null;
}

/**
 * Check if release posts directory has content.
 *
 * @return bool True if release posts exist
 */
function check_release_posts_exist() {
    $release_posts_dir = 'release-posts';

    if (!is_dir($release_posts_dir)) {
        return false;
    }

    $files = glob("{$release_posts_dir}/*.txt");
    return !empty($files);
}

/**
 * Print usage help.
 *
 * @return void
 */
function print_help() {
    echo "Fetch WooCommerce release data for Claude analysis\n\n";
    echo "Usage:\n";
    echo "  php audit-release-prs.php [options]\n\n";
    echo "Options:\n";
    echo "  --fetch-posts       Fetch release posts from developer blog\n";
    echo "  --fetch-changelog   Fetch changelog from GitHub\n";
    echo "  --version=X.X.X     WooCommerce version (e.g. 9.9.0)\n";
    echo "  --check             Check if required data files exist\n";
    echo "  --help              Show this help message\n\n";
    echo "After fetching data, analyze with Claude skills:\n";
    echo "  /woocommerce-pr-analyzer <version>   - Full thematic analysis\n";
    echo "  /woocommerce-release-comms <version> - Quick relevance scoring\n";
}

/**
 * Main function.
 *
 * @return void
 */
function main() {
    global $argc, $argv;

    // Parse command line options
    $options = getopt('', ['fetch-posts', 'fetch-changelog', 'version:', 'check', 'help']);

    $fetch_posts = isset($options['fetch-posts']);
    $fetch_changelog = isset($options['fetch-changelog']);
    $version = $options['version'] ?? null;
    $check = isset($options['check']);
    $help = isset($options['help']);

    if ($help) {
        print_help();
        return;
    }

    // Get version input if not provided as argument
    if (!$version && ($fetch_changelog || $check)) {
        echo "Enter WooCommerce version (e.g. 9.9.0): ";
        $version = trim(fgets(STDIN));
    }

    // Check mode - just verify files exist
    if ($check) {
        echo "\nChecking data files for version {$version}...\n";

        $changelog_path = check_changelog_exists($version);
        if ($changelog_path) {
            echo "  Changelog: {$changelog_path}\n";
        } else {
            echo "  Changelog: NOT FOUND\n";
            echo "    Run: php fetch-changelog.php {$version}\n";
        }

        if (check_release_posts_exist()) {
            echo "  Release posts: release-posts/ (found)\n";
        } else {
            echo "  Release posts: NOT FOUND\n";
            echo "    Run: php fetch-posts.php\n";
        }

        if ($changelog_path && check_release_posts_exist()) {
            echo "\nData ready! Analyze with:\n";
            echo "  /woocommerce-pr-analyzer {$version}\n";
            echo "  /woocommerce-release-comms {$version}\n";
        }
        return;
    }

    // Fetch release posts if requested
    if ($fetch_posts) {
        echo "Fetching release posts...\n";
        if (!run_script('fetch-posts.php')) {
            echo "Failed to fetch release posts\n";
            return;
        }
    }

    // Fetch changelog if requested
    if ($fetch_changelog) {
        if (!$version) {
            echo "Error: --version required when using --fetch-changelog\n";
            return;
        }
        echo "Fetching changelog for version {$version}...\n";
        if (!run_script('fetch-changelog.php', [$version])) {
            echo "Failed to fetch changelog\n";
            return;
        }
    }

    // If no flags provided, show help
    if (!$fetch_posts && !$fetch_changelog && !$check) {
        print_help();
        echo "\n" . str_repeat('=', 60) . "\n";
        echo "Quick Start:\n";
        echo str_repeat('=', 60) . "\n";
        echo "\n1. Fetch data:\n";
        echo "   php audit-release-prs.php --fetch-changelog --fetch-posts --version=9.9.0\n";
        echo "\n2. Analyze with Claude:\n";
        echo "   /woocommerce-pr-analyzer 9.9.0\n";
        echo "\n3. Or for quick scoring:\n";
        echo "   /woocommerce-release-comms 9.9.0\n";
        return;
    }

    // Show next steps
    echo "\n" . str_repeat('=', 60) . "\n";
    echo "Data fetched successfully!\n";
    echo str_repeat('=', 60) . "\n";

    if ($version) {
        $changelog_path = check_changelog_exists($version);
        if ($changelog_path) {
            echo "\nChangelog: {$changelog_path}\n";
        }
    }

    if (check_release_posts_exist()) {
        echo "Release posts: release-posts/\n";
    }

    echo "\nNext steps - analyze with Claude:\n";
    if ($version) {
        echo "  /woocommerce-pr-analyzer {$version}   - Full thematic analysis\n";
        echo "  /woocommerce-release-comms {$version} - Quick relevance scoring\n";
    } else {
        echo "  /woocommerce-pr-analyzer <version>   - Full thematic analysis\n";
        echo "  /woocommerce-release-comms <version> - Quick relevance scoring\n";
    }
}

// Main execution
if (php_sapi_name() === 'cli') {
    main();
}
