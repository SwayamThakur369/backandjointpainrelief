import os
import re
from bs4 import BeautifulSoup

# Paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = SCRIPT_DIR
LAYOUT_PATH = os.path.join(SITE_ROOT, "layout.html")

# Directories and files to exclude from processing
EXCLUDE_DIRS = [".git", "hts-cache", "wp-admin", "wp-json", "wp-includes"]
EXCLUDE_FILES = ["layout.html", "backandjointpainrelief.whtt", "backblue.gif", "fade.gif", "cookies.txt", "hts-log.txt", "xmlrpc0db0.php"]

# List of service slugs to help identify condition pages
SERVICE_SLUGS = [
    "trigger-points", "lumbar-epidural-injection", "caudal-epidural-injections",
    "facet-joints-intra-articular-injections", "selective-nerve-root-blocks",
    "sacro-illiac-joint-injections", "intra-articular-injections",
    "visco-durolene-synvisc-monovisc-prp-injections", "tennis-elbow",
    "frozen-shoulder", "rotator-cuff-tendinopathy", "plantar-fasciitis",
    "carpal-tunnel-syndrome", "plaster-application", "scotch-cast-application",
    "splint-application", "golfers-elbow", "trigger-finger"
]

def get_depth_prefix(filepath):
    """Calculates relative path prefix based on file depth relative to SITE_ROOT."""
    abs_filepath = os.path.abspath(filepath)
    abs_site_root = os.path.abspath(SITE_ROOT)
    relative_path = os.path.relpath(abs_filepath, abs_site_root)
    parts = re.split(r'[\\/]', relative_path)
    depth = len(parts) - 1
    if depth <= 0:
        return "./"
    return "../" * depth

def clean_content_text(soup_content):
    """Strips PageLayer styles, empty elements, and garbage markup."""
    # Remove inline style tags
    for style_tag in soup_content.find_all("style"):
        style_tag.decompose()
    
    # Remove script tags
    for script_tag in soup_content.find_all("script"):
        script_tag.decompose()
        
    # Remove empty divs or wrappers
    for div in soup_content.find_all("div"):
        if not div.get_text(strip=True) and not div.find_all(["img", "iframe", "video"]):
            div.decompose()
            
    return soup_content

def extract_condition_details(main_soup):
    """Parses a condition page to extract title, paragraphs, images, and video frames."""
    title_el = main_soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else "Treatment Service"
    
    # Extract video embeds
    videos = []
    for iframe in main_soup.find_all("iframe"):
        src = iframe.get("src", "")
        if "youtube" in src or "vimeo" in src:
            videos.append(iframe)
            
    # Extract images (excluding icons and tracking pixels)
    images = []
    for img in main_soup.find_all("img"):
        src = img.get("src", "")
        if src and not any(x in src.lower() for x in ["cropped-", "logo", "badge", "avatar"]):
            images.append(img)
            
    # Extract body paragraphs
    paragraphs = []
    for el in main_soup.find_all(["p", "div"]):
        is_text_container = False
        if el.name == "p":
            is_text_container = True
        elif el.name == "div" and any(cls in el.get("class", []) for cls in ["pagelayer-heading-holder", "pagelayer-wp-text"]):
            # Avoid duplicate nesting by checking for child text containers
            if not el.find(["p", "div"]):
                is_text_container = True
            elif el.find(["h1", "h2", "h3", "h4", "h5", "h6"]) and not el.find("p"):
                is_text_container = True
                
        if is_text_container:
            txt = el.get_text(strip=True)
            if txt and len(txt) > 20: # Skip small placeholder/nav paragraphs
                # Skip generated template text
                if "Get back to living pain-free" in txt:
                    continue
                if "Ortho Cure & Pain Relief Clinic" in txt:
                    continue
                if "Call: 8237073397" in txt:
                    continue
                paragraphs.append(el)
            
    return title, paragraphs, images, videos

def rebuild_service_page(title, paragraphs, images, videos, prefix):
    """Generates standard premium layout for service pages."""
    html_content = f"""
    <div class="section hero-slider" style="background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light)); padding: 40px 0; color: white; text-align: center;">
      <div class="container">
        <h1 style="color: white; margin-bottom: 10px; font-size: 2.75rem;">{title}</h1>
        <p style="font-size: 1.1rem; opacity: 0.9; max-width: 600px; margin: 0 auto;">Dr. Paradkar’s Ortho Cure & Pain Relief Clinic</p>
      </div>
    </div>
    
    <div class="section container">
      <div class="grid grid-2">
        <div class="service-details-column">
          <h2 style="margin-top: 0; font-size: 1.75rem; margin-bottom: 20px;">Condition & Treatment Overview</h2>
    """
    
    # Add paragraphs
    for p in paragraphs:
        if p.find(["h1", "h2", "h3", "h4", "h5", "h6"]):
            heading_el = p.find(["h1", "h2", "h3", "h4", "h5", "h6"])
            p_str = f'<h3 class="text-xl font-bold text-primary mt-6 mb-3">{heading_el.get_text(strip=True)}</h3>'
        else:
            p_str = f'<p class="mb-4 text-on-surface-variant text-base leading-relaxed">{p.get_text(strip=True)}</p>'
        
        p_str = p_str.replace("https://backandjointpainrelief.com/", prefix)
        html_content += f"      {p_str}\n"
        
    html_content += """
        </div>
        
        <div class="service-media-column" style="display: flex; flex-direction: column; gap: 30px;">
    """
    
    # Add Video Card
    if videos:
        vid_src = videos[0].get("src", "")
        html_content += f"""
          <div class="card" style="padding: 15px;">
            <h3 style="margin-top: 0; font-size: 1.25rem; margin-bottom: 15px;"><i class="fas fa-video" style="color: var(--color-accent); margin-right: 8px;"></i>Condition Video</h3>
            <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 8px; border: 1px solid var(--color-border);">
              <iframe src="{vid_src}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" allowfullscreen></iframe>
            </div>
          </div>
        """
    # Add Image Card if no video or if additional media exists
    elif images:
        img_src = images[0].get("src", "")
        html_content += f"""
          <div class="card" style="padding: 15px; text-align: center;">
            <img src="{img_src}" alt="{title}" style="max-width: 100%; height: auto; border-radius: 8px; border: 1px solid var(--color-border);" />
          </div>
        """
        
    # Add Call to Action Card
    html_content += f"""
          <div class="card" style="background-color: var(--color-primary); color: white;">
            <h3 style="color: white; margin-top: 0;"><i class="fas fa-calendar-check" style="color: var(--color-accent-light); margin-right: 8px;"></i>Schedule an Appointment</h3>
            <p style="color: #cbd5e0; font-size: 14px; margin-bottom: 20px;">Get back to living pain-free. Book your consult session at our Bavdhan or Kothrud clinics.</p>
            <div style="display: flex; flex-direction: column; gap: 12px;">
              <a href="{prefix}contact/index.html" class="btn btn-primary" style="width: 100%; text-align: center;">Book Consultation Now</a>
              <div style="font-size: 13px; color: #cbd5e0; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px;">
                <i class="fas fa-phone-alt"></i> Call: 8237073397 / 9356576087
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    """
    return html_content

def process_file(filepath, compile_all=False):
    """Processes a single HTML page and builds the redesigned version."""
    prefix = get_depth_prefix(filepath)
    relative_path = os.path.relpath(filepath, SITE_ROOT)
    
    # If not compile_all and it is not the homepage, skip for initial review
    is_home = relative_path == "index.html" or relative_path == "." or filepath == os.path.join(SITE_ROOT, "index.html")
    if not compile_all and not is_home:
        print(f"Skipping {relative_path} (Waiting for initial homepage review)")
        return
        
    print(f"Processing: {relative_path}")
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        
    # Get title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "Dr. Paradkar’s Ortho Cure & Pain Relief Clinic"
    
    # Extract main content area
    main_section = soup.find("main")
    if not main_section:
        print(f"Error: No <main> container found in {relative_path}")
        return
        
    clean_main = clean_content_text(main_section)
    
    # Check if this is a nested service condition page
    parent_dir = os.path.basename(os.path.dirname(filepath))
    is_service = parent_dir in SERVICE_SLUGS
    
    if is_service:
        # Standardize the services page layout
        title_extracted, paragraphs, images, videos = extract_condition_details(clean_main)
        content_html = rebuild_service_page(title_extracted, paragraphs, images, videos, prefix)
    else:
        # Keep original structure but clean PageLayer inline css/styles
        # We will wrap it in standard containers to clean up
        content_html = str(clean_main)
        # Normalize absolute URLs
        content_html = content_html.replace("https://backandjointpainrelief.com/", prefix)
        
    # Read layout template
    with open(LAYOUT_PATH, 'r', encoding='utf-8') as f:
        layout_html = f.read()
        
    # Insert template variables
    built_page = layout_html
    built_page = built_page.replace("{{TITLE}}", title)
    built_page = built_page.replace("{{PREFIX}}", prefix)
    built_page = built_page.replace("{{CONTENT}}", content_html)
    built_page = built_page.replace("{{EXTRA_HEAD}}", "")
    built_page = built_page.replace("{{EXTRA_SCRIPTS}}", "")
    
    # Write backcompiled file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(built_page)
        
    print(f"Successfully compiled {relative_path}!")

def main(compile_all=False):
    """Walks the folder structure and processes the target HTML pages."""
    for root, dirs, files in os.walk(SITE_ROOT):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        
        for file in files:
            if file.endswith(".html") and file not in EXCLUDE_FILES:
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, SITE_ROOT).replace("\\", "/")
                if rel_path in ["contact/index.html", "gallery/index.html", "about/index.html", "services/index.html", "index.html"]:
                    print(f"Excluding customized page: {rel_path}")
                    continue
                process_file(filepath, compile_all)

if __name__ == "__main__":
    import sys
    compile_all_flag = "--all" in sys.argv
    main(compile_all_flag)
