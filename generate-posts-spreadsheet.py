import requests
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
import html
import os

def fetch_posts(wp_site_url, per_page=10, page=1):
    """Fetch posts from WordPress REST API"""
    endpoint = f"{wp_site_url}/wp-json/wp/v2/posts"
    params = {
        'per_page': per_page,  # Changed to 10 for public API
        'page': page,
        'after': (datetime.now() - timedelta(days=365)).isoformat(),
        '_fields': 'title,date,categories'
    }
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        
        # Get total pages from headers
        total_pages = int(response.headers.get('X-WP-TotalPages', 1))
        
        return {
            'posts': response.json(),
            'total_pages': total_pages
        }
    except requests.RequestException as e:
        print(f"Error fetching posts: {e}")
        return {'posts': [], 'total_pages': 0}

def get_category_names(wp_site_url, category_ids):
    """Fetch category names for given category IDs"""
    endpoint = f"{wp_site_url}/wp-json/wp/v2/categories"
    params = {'include': ','.join(map(str, category_ids))}
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        categories = response.json()
        return {cat['id']: cat['name'] for cat in categories}
    except requests.RequestException as e:
        print(f"Error fetching categories: {e}")
        return {}

def clean_text(text):
    """Clean and normalize text for proper display"""
    # Decode HTML entities
    text = html.unescape(text)
    return text

def ensure_export_dir():
    """Ensure exports directory exists"""
    export_dir = 'exports'
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    return export_dir

def main():
    # Replace with your WordPress site URL
    wp_site_url = "https://developer.woocommerce.com"
    
    # Ensure exports directory exists
    export_dir = ensure_export_dir()
    
    # Fetch all posts from the last year
    all_posts = []
    page = 1
    print("Fetching posts...")
    
    # Get first page and total pages
    result = fetch_posts(wp_site_url, page=page)
    all_posts.extend(result['posts'])
    total_pages = result['total_pages']
    
    # Fetch remaining pages
    for page in range(2, total_pages + 1):
        print(f"Fetching page {page} of {total_pages}...")
        result = fetch_posts(wp_site_url, page=page)
        all_posts.extend(result['posts'])
    
    print(f"Found {len(all_posts)} posts")

    if not all_posts:
        print("No posts found. Exiting.")
        return

    # Get unique category IDs from all posts
    category_ids = set()
    for post in all_posts:
        category_ids.update(post['categories'])

    # Get category names
    print("Fetching category information...")
    category_names = get_category_names(wp_site_url, category_ids)

    # Create a dictionary to store posts by category and month
    posts_by_category = defaultdict(lambda: defaultdict(list))

    # Process posts
    print("Processing posts...")
    for post in all_posts:
        post_date = datetime.fromisoformat(post['date'].replace('Z', '+00:00'))
        month_year = post_date.strftime('%B %Y')
        
        # Add post to each of its categories
        for cat_id in post['categories']:
            cat_name = category_names.get(cat_id, f'Category {cat_id}')
            # Clean the post title before adding it
            clean_title = clean_text(post['title']['rendered'])
            posts_by_category[cat_name][month_year].append(clean_title)

    # Get sorted list of unique month/years
    all_months = sorted(set(
        month for cat_posts in posts_by_category.values() 
        for month in cat_posts.keys()
    ), key=lambda x: datetime.strptime(x, '%B %Y'))

    # Create DataFrame
    print("Creating CSV file...")
    df_data = {}
    for month in all_months:
        row_data = []
        for category in posts_by_category:
            posts_titles = posts_by_category[category][month]
            # Join multiple posts with newlines
            row_data.append('\n'.join(posts_titles) if posts_titles else '')
        df_data[month] = row_data

    # Create DataFrame with months as index and categories as columns
    df = pd.DataFrame(df_data, index=list(posts_by_category.keys())).T

    # Save to CSV with proper handling of newlines and encoding
    output_file = os.path.join(export_dir, 'wordpress_posts_by_category.csv')
    df.to_csv(output_file, encoding='utf-8-sig', quoting=1)  # utf-8-sig adds BOM for Excel
    print(f"CSV file has been created: {output_file}")
    print("\nNote: When opening in Excel, you may need to:")
    print("1. Use 'Data' > 'From Text/CSV'")
    print("2. Set the delimiter to comma")
    print("3. Enable 'Treat consecutive delimiters as one'")
    print("4. Set the text qualifier to double quotes")
    print("5. Set the encoding to '65001: Unicode (UTF-8)'")

if __name__ == "__main__":
    main()
