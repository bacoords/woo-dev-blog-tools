#!/usr/bin/env php
<?php
/**
 * Fetch release posts from the WooCommerce developer blog.
 *
 * Usage: php fetch-posts.php
 *
 * This script fetches posts from the "Release Posts" category on
 * developer.woocommerce.com and saves them as text files.
 */

require_once __DIR__ . '/includes/functions.php';

define('WP_SITE_URL', 'https://developer.woocommerce.com');
define('RELEASE_POSTS_DIR', __DIR__ . '/release-posts');

/**
 * Get date from post and format it as YYYY-MM-DD.
 *
 * @param array $post The post data
 * @return string The formatted date
 */
function get_date_from_post($post) {
    $date = new DateTime($post['date']);
    return $date->format('Y-m-d');
}

/**
 * Fetch and save release posts from WordPress.
 *
 * @return void
 */
function fetch_and_save_posts() {
    $base_url = WP_SITE_URL . '/wp-json/wp/v2';

    // First, get the category ID for 'Release Posts'
    $categories_url = "{$base_url}/categories";
    $categories_response = wordpress_request($categories_url, ['per_page' => 100]);
    $categories = json_decode($categories_response, true);

    if (!is_array($categories)) {
        echo "Error fetching categories\n";
        return;
    }

    // Find the Release Posts category
    $release_posts_category = null;
    foreach ($categories as $cat) {
        if ($cat['name'] === 'Release Posts') {
            $release_posts_category = $cat;
            break;
        }
    }

    if (!$release_posts_category) {
        echo "Could not find 'Release Posts' category\n";
        return;
    }

    // Get posts from the Release Posts category
    $posts_url = "{$base_url}/posts";
    $params = [
        'categories' => $release_posts_category['id'],
        'per_page' => 100,
        'orderby' => 'date',
        'order' => 'desc'
    ];

    $posts_response = wordpress_request($posts_url, $params);
    $posts = json_decode($posts_response, true);

    if (!is_array($posts)) {
        echo "Error fetching posts\n";
        return;
    }

    // Create release-posts directory if it doesn't exist
    ensure_directory(RELEASE_POSTS_DIR);

    // Get list of existing files to avoid duplicates
    $existing_files = [];
    if (is_dir(RELEASE_POSTS_DIR)) {
        $existing_files = scandir(RELEASE_POSTS_DIR);
    }

    // Process each post
    foreach ($posts as $post) {
        // Get the date and title
        $post_date = get_date_from_post($post);
        $title = html_entity_decode($post['title']['rendered'], ENT_QUOTES | ENT_HTML5, 'UTF-8');

        // Skip posts with specific terms in the title
        $skip_terms = ['woocommerce-blocks', 'delayed', 'dot-release'];
        $sanitized_title = sanitize_filename($title);
        $should_skip = false;
        foreach ($skip_terms as $term) {
            if (stripos($sanitized_title, strtolower($term)) !== false) {
                $should_skip = true;
                break;
            }
        }

        if ($should_skip) {
            echo "Skipping filtered post: {$title}\n";
            continue;
        }

        // Create a filename with date prefix
        $filename = "{$post_date}-{$sanitized_title}.txt";

        // Skip if we've already processed this post
        if (in_array($filename, $existing_files)) {
            echo "Skipping already processed post: {$title}\n";
            continue;
        }

        // Prepare the content
        $content = "Title: {$title}\n";
        $content .= "Date: {$post['date']}\n";
        $content .= "Link: {$post['link']}\n";
        $content .= "\nContent:\n";

        // Convert HTML to text (similar to html2text)
        $markdown_content = html_to_text($post['content']['rendered']);
        $content .= $markdown_content;

        // Save to file
        $filepath = RELEASE_POSTS_DIR . '/' . $filename;
        if (file_put_contents($filepath, $content) !== false) {
            echo "Saved post: {$title}\n";
        } else {
            echo "Error saving post: {$title}\n";
        }
    }
}

// Main execution
if (php_sapi_name() === 'cli') {
    fetch_and_save_posts();
}
