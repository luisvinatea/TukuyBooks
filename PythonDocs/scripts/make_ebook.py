"""make_ebook.py
This script creates an EPUB file from the scraped Python documentation.
It reads the scraped data from a JSON Lines file, processes the content,
and generates an EPUB file with proper internal linking and structure.
Usage:
    python make_ebook.py
"""
import json
import os
from ebooklib import epub
from bs4 import BeautifulSoup
from bs4.element import Tag

# Add module-level anchor map constant for internal link mapping
ANCHOR_MAP = {
    'library-index': 'the-python-standard-library',
    'reference-index': 'the-python-language-reference',
    'extending-index': 'extending-and-embedding-the-python-interpreter',
    'c-api-index': 'python-c-api-reference-manual'
}


def load_chapters(input_file):
    """Load and sort chapters from JSON Lines file."""
    chapters = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            chapters.append(json.loads(line))
    chapters.sort(key=lambda x: (x.get('priority', 999), x.get('level', 1)))
    return chapters


def init_book():
    """Initialize and return a new EpubBook with metadata."""
    book = epub.EpubBook()
    book.set_identifier('python3docs')
    book.set_title('Python 3.13.2 Documentation')
    book.set_language('en')
    book.add_author('Python Software Foundation')
    return book


def create_items(chapters, book):
    """Create EpubHtml items, map URLs to filenames, and add to book."""
    url_to_filename = {}
    epub_chapters = []
    for i, chap in enumerate(chapters):
        fname = f'chap_{i+1}.xhtml'
        url_to_filename[chap['url']] = fname
        item = epub.EpubHtml(title=chap['title'], file_name=fname, lang='en')
        epub_chapters.append(item)
        book.add_item(item)
    return url_to_filename, epub_chapters


# Helper to rewrite internal hrefs, reducing local variables in main function
def rewrite_href(raw_href, url_to_filename, chapters, internal_links):
    """Rewrite hrefs to point to the correct internal links."""
    # Normalize href to string
    if isinstance(raw_href, (list, tuple)):
        href = raw_href[0] or ''
    else:
        href = raw_href or ''
    if not isinstance(href, str):
        href = str(href)
    # Skip external links and anchors
    if href.startswith(('http://', 'https://', 'mailto:', '#')):
        return None
    base, fragment = (href.split('#', 1) + [''])[:2]
    fragment = '#' + fragment if fragment else ''
    # Map known anchors
    if fragment[1:] in ANCHOR_MAP:
        fragment = '#' + ANCHOR_MAP[fragment[1:]]
    # Direct URL mapping
    match = next((u for u in url_to_filename if base in u), None)
    if match:
        return url_to_filename[match] + fragment
    # Title-based internal links
    tgt = internal_links.get(href)
    if tgt:
        for o in chapters:
            if o['title'] == tgt:
                return url_to_filename[o['url']] + fragment
    return None


# Refactor fix_internal_links to use helper
def fix_internal_links(chapters, epub_chapters, url_to_filename):
    """Update internal links in each chapter content."""
    for idx, chap in enumerate(chapters):
        soup = BeautifulSoup(chap['content'], 'html.parser')
        for element in soup.find_all('a', class_='reference internal'):
            if not isinstance(element, Tag):
                continue
            raw_href = element.attrs.get('href', '')
            new_href = rewrite_href(
                raw_href,
                url_to_filename,
                chapters,
                chap.get('internal_links', {})
            )
            if new_href:
                element.attrs['href'] = new_href
        epub_chapters[idx].content = str(soup).encode('utf-8')
    return epub_chapters


def finalize_and_write(book, epub_chapters, output_path):
    """Assemble table of contents, spine, and write EPUB file."""
    book.toc = epub_chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + epub_chapters
    epub.write_epub(output_path, book)


def create_ebook():
    """Create an EPUB file from the scraped Python documentation."""
    # Initialize paths and validate input
    input_file = os.path.join("./outputs", "python_docs.jl")
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Run the spider first.")
        return
    # Load and prepare data
    chapters = load_chapters(input_file)
    book = init_book()
    mappings, items = create_items(chapters, book)
    processed = fix_internal_links(chapters, items, mappings)
    # Write EPUB
    output_path = os.path.join("./outputs", "Python3Docs.epub")
    finalize_and_write(book, processed, output_path)
    print(f"EPUB created at: {output_path}")


if __name__ == "__main__":
    create_ebook()
