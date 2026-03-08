#!/usr/bin/env python3
"""
Validate per-paper HTML pages and PDFs for scholarly metadata.
Generates a short report at /tmp/scholar_validation_report.txt and prints a summary.
Run inside the project's virtualenv (created previously at .venv).
"""
import re
from pathlib import Path
import sys

ROOT = Path('/Users/darshanbmehta/gs refresh/github-pages-site')
PAPERS = ROOT / 'papers'
REPORT = Path('/tmp/scholar_validation_report.txt')

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

html_files = sorted(p for p in PAPERS.iterdir() if p.suffix.lower() == '.html')
pdf_files = sorted(p for p in PAPERS.iterdir() if p.suffix.lower() == '.pdf')

missing_author_pages = []
pages_with_authors = []
for h in html_files:
    txt = h.read_text(encoding='utf-8')
    # find citation_author meta tags
    authors = re.findall(r'<meta\s+name=["\']citation_author["\']\s+content=["\']([^"\']+)["\']', txt, flags=re.IGNORECASE)
    if authors:
        pages_with_authors.append((h.name, authors))
    else:
        missing_author_pages.append(h.name)

pdfs_missing_metadata = []
pdfs_with_metadata = []
if PdfReader is None:
    pdfs_note = 'pypdf not available in this interpreter; cannot inspect PDF metadata.'
else:
    pdfs_note = ''
    for p in pdf_files:
        try:
            reader = PdfReader(str(p))
            info = reader.metadata
            title = None
            author = None
            if info:
                title = getattr(info, 'title', None) or (info.get('/Title') if isinstance(info, dict) else None)
                author = getattr(info, 'author', None) or (info.get('/Author') if isinstance(info, dict) else None)
            if not title and not author:
                pdfs_missing_metadata.append(p.name)
            else:
                pdfs_with_metadata.append((p.name, title, author))
        except Exception as e:
            pdfs_missing_metadata.append(p.name + ' (error: ' + str(e) + ')')

# write report
with REPORT.open('w', encoding='utf-8') as f:
    f.write('Scholar metadata validation report\n')
    f.write('Project: ' + str(ROOT) + '\n\n')
    f.write('HTML pages checked: %d\n' % len(html_files))
    f.write(' - pages with citation_author: %d\n' % len(pages_with_authors))
    f.write(' - pages missing citation_author: %d\n\n' % len(missing_author_pages))
    if missing_author_pages:
        f.write('Examples (first 50) of pages missing citation_author:\n')
        for name in missing_author_pages[:50]:
            f.write(' - ' + name + '\n')
        f.write('\n')

    f.write('PDFs checked: %d\n' % len(pdf_files))
    if PdfReader is None:
        f.write(' Note: pypdf not available; PDF metadata not inspected.\n')
    else:
        f.write(' - PDFs with Title/Author metadata: %d\n' % len(pdfs_with_metadata))
        f.write(' - PDFs missing metadata: %d\n\n' % len(pdfs_missing_metadata))
        if pdfs_missing_metadata:
            f.write('Examples (first 50) of PDFs missing Title/Author metadata or errors:\n')
            for name in pdfs_missing_metadata[:50]:
                f.write(' - ' + name + '\n')
            f.write('\n')

    f.write('End of report.\n')

# print concise summary to stdout
print('Report written to', REPORT)
print('HTML pages:', len(html_files), 'pages with author meta:', len(pages_with_authors), 'missing:', len(missing_author_pages))
if PdfReader is None:
    print('PDF metadata: pypdf not available in this interpreter; run inside .venv to inspect PDFs')
else:
    print('PDFs:', len(pdf_files), 'with metadata:', len(pdfs_with_metadata), 'missing:', len(pdfs_missing_metadata))

# exit codes: 0 OK
sys.exit(0)
