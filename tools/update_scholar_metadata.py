#!/usr/bin/env python3
"""
Scan papers/, read PDF metadata, slugify PDF filenames, create/update per-paper HTML pages
with citation meta tags (including citation_author when available), and update sitemap.xml.
Also embed Title/Author metadata into PDF files when available from the HTML pages.
Run from the repository root. Requires pypdf (pip install pypdf).
"""
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path('/Users/darshanbmehta/gs refresh/github-pages-site')
PAPERS = ROOT / 'papers'
SITEMAP = ROOT / 'sitemap.xml'
BASE_URL = 'https://vkolluru1974.github.io/IEEE-2025/papers/'


def slugify(s: str) -> str:
    s = s or ''
    s = s.strip().lower()
    s = re.sub(r'[\r\n\t]+', ' ', s)
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'-{2,}', '-', s)
    s = s.strip('-')
    return s or 'paper'


try:
    from pypdf import PdfReader, PdfWriter
except Exception:
    PdfReader = None
    PdfWriter = None


def read_pdf_metadata(path: Path):
    title = None
    author = None
    if PdfReader is None:
        return title, author
    try:
        reader = PdfReader(str(path))
        info = reader.metadata
        if info:
            # pypdf metadata attributes may vary; fallback to dict access
            title = getattr(info, 'title', None) or (info.get('/Title') if isinstance(info, dict) else None)
            author = getattr(info, 'author', None) or (info.get('/Author') if isinstance(info, dict) else None)
    except Exception:
        pass
    return title, author


def read_metadata_from_html(slug: str):
    """Parse the generated HTML page for citation_title and citation_author meta tags."""
    html_path = PAPERS / f"{slug}.html"
    if not html_path.exists():
        return None, None
    text = html_path.read_text(encoding='utf-8')
    title = None
    authors = []
    for m in re.finditer(r"<meta\s+name=['\"]citation_title['\"]\s+content=['\"]([^'\"]+)['\"]", text, flags=re.IGNORECASE):
        title = title or m.group(1).strip()
    for m in re.finditer(r"<meta\s+name=['\"]citation_author['\"]\s+content=['\"]([^'\"]+)['\"]", text, flags=re.IGNORECASE):
        authors.append(m.group(1).strip())
    author = '; '.join(authors) if authors else None
    return title, author


def embed_pdf_metadata(path: Path, title: str = None, author: str = None):
    """Embed Title and Author into a PDF file using pypdf. Overwrites the file in-place via a temp file.
    If both title and author are None, do nothing. Returns True if file was modified.
    """
    if PdfReader is None or PdfWriter is None:
        print('pypdf not available; cannot embed PDF metadata.')
        return False
    if not title and not author:
        return False
    try:
        reader = PdfReader(str(path))
        writer = PdfWriter()
        # copy pages
        for p in reader.pages:
            writer.add_page(p)
        # existing metadata
        md = {}
        try:
            existing = reader.metadata
            if existing:
                # existing may be Mapping-like
                for k, v in (existing.items() if isinstance(existing, dict) else []):
                    md[k] = v
        except Exception:
            pass
        # use PDF metadata keys
        if title:
            md['/Title'] = title
        if author:
            md['/Author'] = author
        writer.add_metadata(md)
        tmp = path.with_suffix('.tmp.pdf')
        with open(tmp, 'wb') as f:
            writer.write(f)
        tmp.replace(path)
        print(f'Embedded metadata into {path.name}: Title="{title}" Author="{author}"')
        return True
    except Exception as e:
        print(f'Failed to embed metadata into {path.name}: {e}')
        return False


def ensure_html_for_slug(slug: str, pdf_name: str, title: str = None, author: str = None):
    html_path = PAPERS / f"{slug}.html"
    pdf_url = BASE_URL + pdf_name
    if html_path.exists():
        text = html_path.read_text(encoding='utf-8')
        inserts = []
        if title and 'name="citation_title"' not in text:
            inserts.append(f'<meta name="citation_title" content="{title}" />')
        if author and 'name="citation_author"' not in text:
            # split common separators
            auths = [a.strip() for a in re.split(r';|\band\b|,', author) if a.strip()]
            for a in auths:
                if f'content="{a}"' not in text:
                    inserts.append(f'<meta name="citation_author" content="{a}" />')
        if 'name="citation_pdf_url"' not in text:
            inserts.append(f'<meta name="citation_pdf_url" content="{pdf_url}" />')
        if inserts:
            # try to inject before </head>
            new_text, n = re.subn(r'(</head>)', '\n  ' + '\n  '.join(inserts) + '\n\\1', text, flags=re.IGNORECASE)
            if n:
                html_path.write_text(new_text, encoding='utf-8')
                print(f'Updated HTML meta for {html_path.name}')
    else:
        title_clean = title or pdf_name.rsplit('.', 1)[0].replace('-', ' ').title()
        auth_meta = ''
        if author:
            auths = [a.strip() for a in re.split(r';|\band\b|,', author) if a.strip()]
            auth_meta = '\n  '.join([f'<meta name="citation_author" content="{a}" />' for a in auths])
        content = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{title_clean}</title>
  <meta name="citation_title" content="{title_clean}" />
  {auth_meta}
  <meta name="citation_pdf_url" content="{pdf_url}" />
</head>
<body>
  <h1>{title_clean}</h1>
  <p><a href="/papers/{pdf_name}">Download PDF</a></p>
</body>
</html>
'''
        html_path.write_text(content, encoding='utf-8')
        print(f'Created HTML {html_path.name}')


def update_sitemap():
    # parse existing sitemap or create one
    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    if SITEMAP.exists():
        try:
            tree = ET.parse(str(SITEMAP))
            root = tree.getroot()
        except Exception:
            root = ET.Element('urlset', xmlns=ns['sm'])
            tree = ET.ElementTree(root)
    else:
        root = ET.Element('urlset', xmlns=ns['sm'])
        tree = ET.ElementTree(root)

    existing = set()
    for url in root.findall('sm:url', ns):
        loc = url.find('sm:loc', ns)
        if loc is not None and loc.text:
            existing.add(loc.text.strip())

    for f in sorted(PAPERS.iterdir()):
        if f.suffix.lower() not in ('.pdf', '.html'):
            continue
        url = BASE_URL + f.name
        if url not in existing:
            u = ET.SubElement(root, 'url')
            ET.SubElement(u, 'loc').text = url
            print(f'Added to sitemap: {url}')
    tree.write(str(SITEMAP), encoding='utf-8', xml_declaration=True)
    print('Sitemap updated')


def main():
    if not PAPERS.exists():
        print('papers/ directory not found. Exiting.')
        return
    for entry in sorted(PAPERS.iterdir()):
        if entry.is_file() and entry.suffix.lower() == '.pdf':
            title, author = read_pdf_metadata(entry)
            # if metadata missing in PDF, try read from existing HTML (which we previously generated)
            base_name = title or entry.stem
            slug = slugify(base_name)
            new_pdf_name = f"{slug}.pdf"
            new_pdf_path = PAPERS / new_pdf_name
            if entry.name != new_pdf_name:
                # avoid clobbering existing
                if new_pdf_path.exists():
                    # append numeric suffix
                    i = 1
                    while True:
                        candidate = PAPERS / f"{slug}-{i}.pdf"
                        if not candidate.exists():
                            new_pdf_name = candidate.name
                            new_pdf_path = candidate
                            slug = f"{slug}-{i}"
                            break
                        i += 1
                print(f'Renaming: {entry.name} -> {new_pdf_name}')
                entry.rename(new_pdf_path)
                entry = new_pdf_path
            # ensure we get metadata from HTML if available
            html_title, html_author = read_metadata_from_html(slug)
            use_title = title or html_title or None
            use_author = author or html_author or None
            # create or update HTML page with metadata
            ensure_html_for_slug(slug, new_pdf_name, use_title, use_author)
            # embed metadata into PDF if we have title/author and it's missing or different
            current_title, current_author = read_pdf_metadata(PAPERS / new_pdf_name)
            # compare and embed if DIFFERENT and we have values
            if (use_title and use_title != (current_title or '')) or (use_author and use_author != (current_author or '')):
                embed_pdf_metadata(PAPERS / new_pdf_name, use_title, use_author)
    update_sitemap()


if __name__ == '__main__':
    main()
