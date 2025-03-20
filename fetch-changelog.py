import requests
import os
import sys

def fetch_changelog(version):
    # Construct the changelog URL
    changelog_url = f"https://raw.githubusercontent.com/woocommerce/woocommerce/refs/heads/release/{version}/plugins/woocommerce/readme.txt"

    try:
        # Fetch the changelog
        response = requests.get(changelog_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Get the content and split at the changelog marker
        content = response.text
        parts = content.split("== Changelog ==")
        
        if len(parts) < 2:
            print("Error: Could not find changelog section in the file")
            return False
        
        # Create changelogs directory if it doesn't exist
        os.makedirs("changelogs", exist_ok=True)
        
        # Save the changelog to a file
        changelog_content = parts[1].strip()
        filename = f"changelogs/{version}.txt"
        
        with open(filename, "w") as f:
            f.write(changelog_content)
        
        print(f"Successfully saved changelog to {filename}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error fetching changelog: {e}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    # If no version provided as argument, ask for it
    version = sys.argv[1] if len(sys.argv) > 1 else input("Enter WooCommerce version (e.g. 9.8): ")
    success = fetch_changelog(version)
    exit(0 if success else 1)