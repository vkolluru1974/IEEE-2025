#!/usr/bin/env python3
"""
Generate per-paper HTML pages with full Google Scholar metadata:
- Highwire Press meta tags (citation_*)
- Dublin Core meta tags (DC.*)
- JSON-LD ScholarlyArticle structured data
- Visible PDF download link

This replicates the pattern from sdcsdl that successfully appears on Google Scholar.
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("pypdf not installed. Run: pip install pypdf")
    exit(1)

def slugify(text):
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def extract_pdf_metadata(pdf_path):
    """Extract title and author from PDF metadata."""
    try:
        reader = PdfReader(pdf_path)
        meta = reader.metadata
        title = None
        author = None
        if meta:
            title = meta.get('/Title', None)
            author = meta.get('/Author', None)
            # Clean up
            if title and isinstance(title, str):
                title = title.strip()
            if author and isinstance(author, str):
                author = author.strip()
        return title, author
    except Exception as e:
        print(f"  Warning: Could not read PDF metadata from {pdf_path}: {e}")
        return None, None

def title_from_filename(filename):
    """Convert filename to a readable title."""
    name = Path(filename).stem
    # Replace hyphens/underscores with spaces
    name = re.sub(r'[-_]+', ' ', name)
    # Title case
    return name.title()

def generate_html_page(pdf_filename, title, authors, base_url, output_dir, publication_date=None):
    """Generate an HTML page with full scholarly metadata."""
    
    slug = Path(pdf_filename).stem
    pdf_url = f"{base_url}/{pdf_filename}"
    html_url = f"{base_url}/{slug}.html"
    
    if not publication_date:
        publication_date = datetime.now().strftime("%Y/%m/%d")
    
    # Parse authors into list
    author_list = []
    if authors:
        # Split by comma, semicolon, or " and "
        author_list = re.split(r'[;,]|\s+and\s+', authors)
        author_list = [a.strip() for a in author_list if a.strip()]
    
    # Generate Highwire meta tags
    highwire_tags = f'''<meta name="citation_title" content="{title}">
'''
    for author in author_list:
        highwire_tags += f'  <meta name="citation_author" content="{author}">\n'
    if not author_list:
        highwire_tags += f'  <meta name="citation_author" content="Unknown Author">\n'
    
    highwire_tags += f'''  <meta name="citation_publication_date" content="{publication_date}">
  <meta name="citation_pdf_url" content="{pdf_url}">
  <meta name="citation_language" content="en">'''

    # Generate Dublin Core meta tags
    dc_tags = f'''<meta name="DC.Title" content="{title}">
'''
    for author in author_list:
        dc_tags += f'  <meta name="DC.Creator.PersonalName" content="{author}">\n'
    if not author_list:
        dc_tags += f'  <meta name="DC.Creator.PersonalName" content="Unknown Author">\n'
    
    dc_date = publication_date.replace('/', '-')
    dc_tags += f'''  <meta name="DC.Date.created" scheme="ISO8601" content="{dc_date}">
  <meta name="DC.Format" scheme="IMT" content="application/pdf">
  <meta name="DC.Language" scheme="ISO639-1" content="en">
  <meta name="DC.Type" content="Text.Serial.Journal">'''

    # Generate JSON-LD
    json_ld_authors = []
    for author in author_list if author_list else ["Unknown Author"]:
        json_ld_authors.append({"@type": "Person", "name": author})
    
    json_ld = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "headline": title,
        "name": title,
        "author": json_ld_authors,
        "datePublished": publication_date.replace('/', '-'),
        "url": html_url,
        "mainEntityOfPage": html_url,
        "encoding": {
            "@type": "MediaObject",
            "contentUrl": pdf_url,
            "encodingFormat": "application/pdf"
        }
    }
    
    # Authors display
    authors_display = ", ".join(author_list) if author_list else "Unknown Author"
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{title}">
  
  <!-- Google Scholar: Highwire Press Tags -->
  {highwire_tags}

  <!-- Dublin Core Metadata -->
  {dc_tags}

  <!-- Canonical URL -->
  <link rel="canonical" href="{html_url}">

  <!-- JSON-LD Structured Data -->
  <script type="application/ld+json">
{json.dumps(json_ld, indent=2)}
  </script>

  <style>
    body {{ font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; margin: 0; padding: 2rem; max-width: 800px; margin: 0 auto; }}
    h1 {{ color: #333; font-size: 1.5rem; }}
    .meta {{ color: #666; margin-bottom: 1rem; }}
    .download {{ margin-top: 2rem; }}
    .download a {{ display: inline-block; padding: 0.75rem 1.5rem; background: #0066cc; color: white; text-decoration: none; border-radius: 4px; }}
    .download a:hover {{ background: #0052a3; }}
    .back {{ margin-top: 2rem; }}
    .back a {{ color: #0066cc; }}
  </style>
</head>
<body>
  <article>
    <h1>{title}</h1>
    <p class="meta"><strong>Authors:</strong> {authors_display}</p>
    <p class="meta"><strong>Date:</strong> {publication_date.replace('/', '-')}</p>
    
    <div class="download">
      <a href="{pdf_url}" target="_blank" rel="noopener">📄 Download PDF</a>
    </div>
    
    <div class="back">
      <a href="./">← Back to Papers</a>
    </div>
  </article>
</body>
</html>
'''
    
    output_path = os.path.join(output_dir, f"{slug}.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return slug, title, authors_display

def generate_sitemap(base_url, pages, pdfs, output_path):
    """Generate sitemap.xml with all HTML pages and PDFs."""
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    sitemap = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
'''.format(base_url=base_url, today=today)
    
    # Add HTML pages
    for slug in pages:
        sitemap += f'''  <url>
    <loc>{base_url}/{slug}.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
'''
    
    # Add PDFs
    for pdf in pdfs:
        sitemap += f'''  <url>
    <loc>{base_url}/{pdf}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
'''
    
    sitemap += '</urlset>\n'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(sitemap)

def generate_index_page(base_url, papers, output_path):
    """Generate an index page listing all papers."""
    
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Research Papers</title>
  <meta name="description" content="Collection of research papers with full citation metadata for Google Scholar indexing.">
  <link rel="canonical" href="{base_url}/">
  <style>
    body {{ font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; margin: 0; padding: 2rem; max-width: 900px; margin: 0 auto; }}
    h1 {{ color: #333; }}
    .paper {{ border-bottom: 1px solid #eee; padding: 1rem 0; }}
    .paper h2 {{ font-size: 1.1rem; margin: 0 0 0.5rem 0; }}
    .paper h2 a {{ color: #0066cc; text-decoration: none; }}
    .paper h2 a:hover {{ text-decoration: underline; }}
    .paper .authors {{ color: #666; font-size: 0.9rem; }}
    .paper .links {{ margin-top: 0.5rem; }}
    .paper .links a {{ color: #0066cc; margin-right: 1rem; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <h1>Research Papers</h1>
  <p>This collection contains {count} research papers. Each paper page includes citation metadata (Highwire Press tags, Dublin Core, and JSON-LD) for Google Scholar indexing.</p>
  
'''.format(base_url=base_url, count=len(papers))
    
    for slug, title, authors in sorted(papers, key=lambda x: x[1].lower()):
        html += f'''  <div class="paper">
    <h2><a href="{slug}.html">{title}</a></h2>
    <p class="authors">{authors}</p>
    <div class="links">
      <a href="{slug}.html">View Details</a>
      <a href="{slug}.pdf">Download PDF</a>
    </div>
  </div>
'''
    
    html += '''
</body>
</html>
'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

def process_directory(input_dir, output_dir, base_url):
    """Process all PDFs in a directory and generate HTML pages."""
    
    print(f"\nProcessing: {input_dir}")
    print(f"Output to: {output_dir}")
    print(f"Base URL: {base_url}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all PDFs
    pdfs = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    print(f"Found {len(pdfs)} PDFs")
    
    papers = []
    pdf_files = []
    
    for pdf in pdfs:
        pdf_path = os.path.join(input_dir, pdf)
        
        # Extract metadata from PDF
        title, authors = extract_pdf_metadata(pdf_path)
        
        # Fallback to filename-based title
        if not title or len(title) < 3:
            title = title_from_filename(pdf)
        
        print(f"  Processing: {pdf}")
        print(f"    Title: {title[:60]}..." if len(title) > 60 else f"    Title: {title}")
        print(f"    Authors: {authors or 'Unknown'}")
        
        # Generate HTML page
        slug, title, authors_display = generate_html_page(
            pdf, title, authors, base_url, output_dir
        )
        
        papers.append((slug, title, authors_display))
        pdf_files.append(pdf)
    
    # Generate index page
    index_path = os.path.join(output_dir, 'index.html')
    generate_index_page(base_url, papers, index_path)
    print(f"\nGenerated index page: {index_path}")
    
    # Generate sitemap
    sitemap_path = os.path.join(output_dir, 'sitemap.xml')
    generate_sitemap(base_url, [p[0] for p in papers], pdf_files, sitemap_path)
    print(f"Generated sitemap: {sitemap_path}")
    
    return papers, pdf_files

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python generate_scholar_pages.py <input_dir> <output_dir> <base_url>")
        print("Example: python generate_scholar_pages.py ./papers ./papers https://user.github.io/repo/papers")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    base_url = sys.argv[3]
    
    process_directory(input_dir, output_dir, base_url)
    print("\nDone!")
