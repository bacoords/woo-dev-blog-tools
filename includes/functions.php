<?php
/**
 * Shared utility functions for WooCommerce Dev Blog Tools
 */

/**
 * Parse a .env file and return an associative array of environment variables.
 *
 * @param string $path Path to the .env file
 * @return array Associative array of environment variables
 */
function parse_env_file($path) {
    if (!file_exists($path)) {
        return [];
    }

    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $env = [];

    foreach ($lines as $line) {
        // Skip comments
        if (strpos(trim($line), '#') === 0) {
            continue;
        }
        // Skip lines without =
        if (strpos($line, '=') === false) {
            continue;
        }

        list($key, $value) = explode('=', $line, 2);
        $key = trim($key);
        $value = trim($value);

        // Remove surrounding quotes
        $value = trim($value, "\"'");

        $env[$key] = $value;
    }

    return $env;
}

/**
 * Make a request to the GitHub API with authentication and rate limit handling.
 *
 * @param string $url The API URL
 * @param string $token The GitHub token
 * @param bool $return_headers Whether to return headers along with the body
 * @return array|string Response body (or array with 'body' and 'headers' if $return_headers is true)
 */
function github_request($url, $token, $return_headers = false) {
    $ch = curl_init($url);

    $headers = [];

    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_HTTPHEADER => [
            "Authorization: Bearer $token",
            "User-Agent: WooDevTools",
            "Accept: application/vnd.github.v3+json"
        ],
        CURLOPT_HEADERFUNCTION => function($curl, $header) use (&$headers) {
            $len = strlen($header);
            $header = explode(':', $header, 2);
            if (count($header) < 2) {
                return $len;
            }
            $headers[strtolower(trim($header[0]))] = trim($header[1]);
            return $len;
        }
    ]);

    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    // Handle rate limit
    if ($http_code === 403) {
        echo "Rate limit hit, waiting 60 seconds...\n";
        sleep(60);
        return github_request($url, $token, $return_headers);
    }

    if ($return_headers) {
        return [
            'body' => $response,
            'headers' => $headers,
            'http_code' => $http_code
        ];
    }

    return $response;
}

/**
 * Make a request to the WordPress REST API.
 *
 * @param string $url The API URL
 * @param array $params Query parameters
 * @param bool $return_headers Whether to return headers along with the body
 * @return array Response with 'body' and optionally 'headers'
 */
function wordpress_request($url, $params = [], $return_headers = false) {
    if (!empty($params)) {
        $url .= '?' . http_build_query($params);
    }

    $ch = curl_init($url);

    $headers = [];

    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_HTTPHEADER => [
            "User-Agent: WooDevTools"
        ],
        CURLOPT_HEADERFUNCTION => function($curl, $header) use (&$headers) {
            $len = strlen($header);
            $header = explode(':', $header, 2);
            if (count($header) < 2) {
                return $len;
            }
            $headers[strtolower(trim($header[0]))] = trim($header[1]);
            return $len;
        }
    ]);

    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($return_headers) {
        return [
            'body' => $response,
            'headers' => $headers,
            'http_code' => $http_code
        ];
    }

    return $response;
}

/**
 * Sanitize a string for use as a filename.
 *
 * @param string $title The title to sanitize
 * @return string The sanitized filename
 */
function sanitize_filename($title) {
    // Remove any non-alphanumeric characters (except spaces and hyphens)
    $filename = preg_replace('/[^\w\s-]/u', '', $title);
    // Replace spaces with hyphens
    $filename = preg_replace('/[-\s]+/', '-', $filename);
    // Convert to lowercase
    return strtolower(trim($filename, '-'));
}

/**
 * Extract the "Changes proposed" section from a PR description.
 *
 * @param string $description The PR description
 * @return string The extracted changes section
 */
function extract_changes_section($description) {
    if (empty($description)) {
        return '';
    }

    // Strip HTML tags
    $description = preg_replace('/<[^>]+>/', '', $description);
    // Unescape HTML entities
    $description = html_entity_decode($description, ENT_QUOTES | ENT_HTML5, 'UTF-8');

    // Find content between "Changes proposed" and "How to test"
    $pattern = '/Changes proposed in this Pull Request:(.*?)(?=How to test the changes in this Pull Request:|\Z)/s';
    if (preg_match($pattern, $description, $matches)) {
        $content = $matches[1];
        // Clean up the content
        $lines = explode("\n", $content);
        $lines = array_map('trim', $lines);
        $lines = array_filter($lines, function($line) {
            return !empty($line) &&
                   strpos($line, '<!--') !== 0 &&
                   substr($line, -3) !== '-->';
        });
        return trim(implode("\n", $lines));
    }

    return '';
}

/**
 * Convert HTML content to plain text.
 *
 * @param string $html The HTML content
 * @return string The plain text content
 */
function html_to_text($html) {
    // Convert headers to text with newlines
    $text = preg_replace('/<h[1-6][^>]*>(.*?)<\/h[1-6]>/is', "\n## $1\n\n", $html);
    // Convert paragraphs to double newlines
    $text = preg_replace('/<\/p>/i', "\n\n", $text);
    // Convert line breaks to newlines
    $text = preg_replace('/<br\s*\/?>/i', "\n", $text);
    // Convert list items
    $text = preg_replace('/<li[^>]*>/i', "* ", $text);
    $text = preg_replace('/<\/li>/i', "\n", $text);
    // Convert links to markdown-style
    $text = preg_replace('/<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)<\/a>/is', '[$2]($1)', $text);
    // Strip remaining tags
    $text = strip_tags($text);
    // Decode HTML entities
    $text = html_entity_decode($text, ENT_QUOTES | ENT_HTML5, 'UTF-8');
    // Clean up excessive newlines
    $text = preg_replace('/\n{3,}/', "\n\n", $text);

    return trim($text);
}

/**
 * Write data to a CSV file with UTF-8 BOM for Excel compatibility.
 *
 * @param string $filename The output filename
 * @param array $headers The column headers
 * @param array $rows The data rows (array of associative arrays)
 * @return bool True on success, false on failure
 */
function write_csv_with_bom($filename, $headers, $rows) {
    $handle = fopen($filename, 'w');
    if (!$handle) {
        return false;
    }

    // Write UTF-8 BOM for Excel compatibility
    fwrite($handle, "\xEF\xBB\xBF");

    // Write headers
    fputcsv($handle, $headers, ',', '"', '\\');

    // Write rows
    foreach ($rows as $row) {
        // Ensure row is in correct order matching headers
        $ordered_row = [];
        foreach ($headers as $header) {
            $ordered_row[] = $row[$header] ?? '';
        }
        fputcsv($handle, $ordered_row, ',', '"', '\\');
    }

    fclose($handle);
    return true;
}

/**
 * Ensure a directory exists, creating it if necessary.
 *
 * @param string $path The directory path
 * @return bool True if directory exists or was created
 */
function ensure_directory($path) {
    if (!is_dir($path)) {
        return mkdir($path, 0755, true);
    }
    return true;
}

/**
 * Parse the Link header from GitHub API responses for pagination.
 *
 * @param string $link_header The Link header value
 * @return string|null The next page URL or null if not found
 */
function parse_next_page_url($link_header) {
    if (empty($link_header)) {
        return null;
    }

    $links = explode(',', $link_header);
    foreach ($links as $link) {
        if (strpos($link, 'rel="next"') !== false) {
            if (preg_match('/<([^>]+)>/', $link, $matches)) {
                return $matches[1];
            }
        }
    }

    return null;
}
