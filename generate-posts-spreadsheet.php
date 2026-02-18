#!/usr/bin/env php
<?php
/**
 * Generate a CSV spreadsheet of blog posts organized by category and month.
 *
 * Usage: php generate-posts-spreadsheet.php
 *
 * This script fetches posts from the WooCommerce developer blog and
 * creates a CSV file with posts grouped by category and month.
 */

require_once __DIR__ . '/includes/functions.php';

define('WP_SITE_URL', 'https://developer.woocommerce.com');

/**
 * Fetch posts from WordPress REST API with pagination info.
 *
 * @param int $per_page Posts per page
 * @param int $page Page number
 * @return array ['posts' => array, 'total_pages' => int]
 */
function fetch_posts($per_page = 10, $page = 1) {
    $endpoint = WP_SITE_URL . '/wp-json/wp/v2/posts';
    $after_date = (new DateTime())->modify('-365 days')->format('c');

    $params = [
        'per_page' => $per_page,
        'page' => $page,
        'after' => $after_date,
        '_fields' => 'title,date,categories'
    ];

    $response = wordpress_request($endpoint, $params, true);

    if ($response['http_code'] !== 200) {
        echo "Error fetching posts: HTTP {$response['http_code']}\n";
        return ['posts' => [], 'total_pages' => 0];
    }

    $posts = json_decode($response['body'], true);
    $total_pages = (int)($response['headers']['x-wp-totalpages'] ?? 1);

    return [
        'posts' => is_array($posts) ? $posts : [],
        'total_pages' => $total_pages
    ];
}

/**
 * Fetch category names for given category IDs.
 *
 * @param array $category_ids Array of category IDs
 * @return array Map of category ID to category name
 */
function get_category_names($category_ids) {
    if (empty($category_ids)) {
        return [];
    }

    $endpoint = WP_SITE_URL . '/wp-json/wp/v2/categories';
    $params = [
        'include' => implode(',', $category_ids)
    ];

    $response = wordpress_request($endpoint, $params);
    $categories = json_decode($response, true);

    if (!is_array($categories)) {
        echo "Error fetching categories\n";
        return [];
    }

    $category_map = [];
    foreach ($categories as $cat) {
        $category_map[$cat['id']] = $cat['name'];
    }

    return $category_map;
}

/**
 * Clean and normalize text for proper display.
 *
 * @param string $text The text to clean
 * @return string The cleaned text
 */
function clean_text($text) {
    return html_entity_decode($text, ENT_QUOTES | ENT_HTML5, 'UTF-8');
}

/**
 * Main function to generate the posts spreadsheet.
 *
 * @return void
 */
function main() {
    // Ensure exports directory exists
    $export_dir = 'exports';
    ensure_directory($export_dir);

    // Fetch all posts from the last year
    $all_posts = [];
    $page = 1;
    echo "Fetching posts...\n";

    // Get first page and total pages
    $result = fetch_posts(10, $page);
    $all_posts = array_merge($all_posts, $result['posts']);
    $total_pages = $result['total_pages'];

    // Fetch remaining pages
    for ($page = 2; $page <= $total_pages; $page++) {
        echo "Fetching page {$page} of {$total_pages}...\n";
        $result = fetch_posts(10, $page);
        $all_posts = array_merge($all_posts, $result['posts']);
    }

    echo "Found " . count($all_posts) . " posts\n";

    if (empty($all_posts)) {
        echo "No posts found. Exiting.\n";
        return;
    }

    // Get unique category IDs from all posts
    $category_ids = [];
    foreach ($all_posts as $post) {
        foreach ($post['categories'] as $cat_id) {
            $category_ids[$cat_id] = true;
        }
    }
    $category_ids = array_keys($category_ids);

    // Get category names
    echo "Fetching category information...\n";
    $category_names = get_category_names($category_ids);

    // Create a dictionary to store posts by category and month
    // Structure: $posts_by_category[$cat_name][$month_year][] = $title
    $posts_by_category = [];

    // Process posts
    echo "Processing posts...\n";
    foreach ($all_posts as $post) {
        $post_date = new DateTime($post['date']);
        $month_year = $post_date->format('F Y');

        // Add post to each of its categories
        foreach ($post['categories'] as $cat_id) {
            $cat_name = $category_names[$cat_id] ?? "Category {$cat_id}";

            // Initialize arrays if needed
            if (!isset($posts_by_category[$cat_name])) {
                $posts_by_category[$cat_name] = [];
            }
            if (!isset($posts_by_category[$cat_name][$month_year])) {
                $posts_by_category[$cat_name][$month_year] = [];
            }

            // Clean the post title before adding it
            $clean_title = clean_text($post['title']['rendered']);
            $posts_by_category[$cat_name][$month_year][] = $clean_title;
        }
    }

    // Get sorted list of unique month/years
    $all_months = [];
    foreach ($posts_by_category as $cat_posts) {
        foreach (array_keys($cat_posts) as $month) {
            $all_months[$month] = true;
        }
    }
    $all_months = array_keys($all_months);

    // Sort by date
    usort($all_months, function($a, $b) {
        $date_a = DateTime::createFromFormat('F Y', $a);
        $date_b = DateTime::createFromFormat('F Y', $b);
        return $date_a <=> $date_b;
    });

    // Get sorted list of categories
    $categories = array_keys($posts_by_category);
    sort($categories);

    // Create CSV file
    echo "Creating CSV file...\n";
    $output_file = "{$export_dir}/wordpress_posts_by_category.csv";

    $handle = fopen($output_file, 'w');
    if (!$handle) {
        echo "Error opening file for writing\n";
        return;
    }

    // Write UTF-8 BOM for Excel compatibility
    fwrite($handle, "\xEF\xBB\xBF");

    // Write header row (empty first column for month, then category names)
    $headers = array_merge(['Month'], $categories);
    fputcsv($handle, $headers, ',', '"', '\\');

    // Write data rows (months as rows, categories as columns)
    foreach ($all_months as $month) {
        $row = [$month];
        foreach ($categories as $category) {
            $posts_titles = $posts_by_category[$category][$month] ?? [];
            // Join multiple posts with newlines
            $row[] = !empty($posts_titles) ? implode("\n", $posts_titles) : '';
        }
        fputcsv($handle, $row, ',', '"', '\\');
    }

    fclose($handle);

    echo "CSV file has been created: {$output_file}\n";
    echo "\nNote: When opening in Excel, you may need to:\n";
    echo "1. Use 'Data' > 'From Text/CSV'\n";
    echo "2. Set the delimiter to comma\n";
    echo "3. Enable 'Treat consecutive delimiters as one'\n";
    echo "4. Set the text qualifier to double quotes\n";
    echo "5. Set the encoding to '65001: Unicode (UTF-8)'\n";
}

// Main execution
if (php_sapi_name() === 'cli') {
    main();
}
