#!/usr/bin/env python3

import requests
import os
import re
from datetime import datetime
from urllib.parse import urlparse
import json
import html2text

def sanitize_filename(title):
    """Convert a title into a valid filename."""
    # Remove any non-alphanumeric characters (except spaces and hyphens)
    filename = re.sub(r'[^\w\s-]', '', title)
    # Replace spaces with hyphens
    filename = re.sub(r'[-\s]+', '-', filename)
    # Convert to lowercase
    return filename.lower()

def get_date_from_post(post):
    """Extract date from post and format it as YYYY-MM-DD."""
    # Parse the date string from the post
    post_date = datetime.strptime(post['date'], '%Y-%m-%dT%H:%M:%S')
    return post_date.strftime('%Y-%m-%d')

def fetch_and_save_posts():
    # WordPress REST API endpoint
    base_url = 'https://developer.woocommerce.com/wp-json/wp/v2'
    
    # First, get the category ID for 'Release Posts'
    categories_url = f'{base_url}/categories'
    categories_response = requests.get(categories_url)
    categories = categories_response.json()
    
    # Find the Release Posts category
    release_posts_category = next(
        (cat for cat in categories if cat['name'] == 'Release Posts'),
        None
    )
    
    if not release_posts_category:
        print("Could not find 'Release Posts' category")
        return
    
    # Get posts from the Release Posts category
    posts_url = f'{base_url}/posts'
    params = {
        'categories': release_posts_category['id'],
        'per_page': 100,  # Adjust this number as needed
        'orderby': 'date',
        'order': 'desc'
    }
    
    posts_response = requests.get(posts_url, params=params)
    posts = posts_response.json()
    
    # Create release-posts directory if it doesn't exist
    output_dir = 'release-posts'
    os.makedirs(output_dir, exist_ok=True)
    
    # Get list of existing files to avoid duplicates
    existing_files = set(os.listdir(output_dir))
    
    # Process each post
    for post in posts:
        # Get the date and title
        post_date = get_date_from_post(post)
        title = post['title']['rendered']
        
        # Skip posts with specific terms in the title
        skip_terms = ['woocommerce-blocks', 'delayed', 'dot-release']
        if any(term.lower() in sanitize_filename(title).lower() for term in skip_terms):
            print(f"Skipping filtered post: {title}")
            continue
        
        # Create a filename with date prefix
        filename = f"{post_date}-{sanitize_filename(title)}.txt"
        
        # Skip if we've already processed this post
        if filename in existing_files:
            print(f"Skipping already processed post: {title}")
            continue
        
        # Prepare the content
        content = f"Title: {title}\n"
        content += f"Date: {post['date']}\n"
        content += f"Link: {post['link']}\n"
        content += "\nContent:\n"
        # Convert HTML to Markdown
        markdown_content = html2text.html2text(post['content']['rendered'])
        content += markdown_content
        
        # Save to file
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Saved post: {title}")

if __name__ == '__main__':
    fetch_and_save_posts()
