import os
from urllib.parse import urlparse
from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = SCRIPT_DIR

EXCLUDE_DIRS = [".git", "hts-cache", "wp-admin", "wp-json", "wp-includes"]
EXCLUDE_FILES = ["layout.html", "backandjointpainrelief.whtt", "backblue.gif", "fade.gif", "cookies.txt", "hts-log.txt", "xmlrpc0db0.php"]

def check_link(file_dir, ref):
    """Resolves a relative link and verifies if the file exists on disk."""
    # Strip query parameters and anchors
    clean_ref = ref.split('?')[0].split('#')[0]
    if not clean_ref:
        return True # Just an anchor on the same page
        
    # Standardize path separators
    clean_ref = clean_ref.replace('/', os.sep)
    
    # Resolve relative path
    target_path = os.path.abspath(os.path.join(file_dir, clean_ref))
    
    # Check if target is a file or a folder containing index.html
    if os.path.exists(target_path):
        return True
    # If the link refers to a directory without index.html explicitly in link, e.g. "about/"
    if os.path.isdir(target_path):
        if os.path.exists(os.path.join(target_path, "index.html")):
            return True
            
    return False

def is_external_or_action(url):
    """Checks if a URL is external, mailto, tel, or dynamic."""
    parsed = urlparse(url)
    if parsed.scheme in ["http", "https", "mailto", "tel"]:
        return True
    if url.startswith("//") or url.startswith("#"):
        return True
    return False

def validate_links():
    broken_links = []
    checked_count = 0
    pages_checked = 0
    
    for root, dirs, files in os.walk(SITE_ROOT):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        
        for file in files:
            if file.endswith(".html") and file not in EXCLUDE_FILES:
                filepath = os.path.join(root, file)
                pages_checked += 1
                
                import warnings
                from bs4 import XMLParsedAsHTMLWarning
                warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
                
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    
                # Find all links and assets
                elements_with_refs = []
                for tag in soup.find_all(True):
                    href = tag.get("href")
                    src = tag.get("src")
                    if href:
                        elements_with_refs.append(("href", href, tag.name))
                    if src:
                        elements_with_refs.append(("src", src, tag.name))
                        
                for attr, val, tag_name in elements_with_refs:
                    if is_external_or_action(val):
                        continue
                        
                    checked_count += 1
                    file_dir = os.path.dirname(filepath)
                    exists = check_link(file_dir, val)
                    
                    if not exists:
                        relative_file = os.path.relpath(filepath, SITE_ROOT)
                        broken_links.append({
                            "page": relative_file,
                            "tag": tag_name,
                            "attribute": attr,
                            "value": val
                        })
                        
    print("\n--- LINK VERIFICATION REPORT ---")
    print(f"Total HTML pages scanned: {pages_checked}")
    print(f"Total local references checked: {checked_count}")
    
    if broken_links:
        print(f"\n[WARNING] Found {len(broken_links)} broken local reference(s):")
        for bl in broken_links:
            print(f"- Page: {bl['page']} | Element: <{bl['tag']} {bl['attribute']}=\"{bl['value']}\"> is broken.")
        return False
    else:
        print("\n[SUCCESS] All internal references, stylesheets, scripts, and image links resolved successfully!")
        return True

if __name__ == "__main__":
    import sys
    success = validate_links()
    sys.exit(0 if success else 1)
