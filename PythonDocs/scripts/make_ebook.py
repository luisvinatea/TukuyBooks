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


def create_ebook():
    """Create an EPUB file from the scraped Python documentation."""
    input_file = os.path.join("./outputs", "python_docs.jl")
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Run the spider first.")
        return

    chapters = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            chapters.append(json.loads(line))

    # Sort chapters by priority and level
    chapters.sort(key=lambda x: (x.get('priority', 999), x.get('level', 1)))

    # Create EPUB
    book = epub.EpubBook()
    book.set_identifier('python3docs')
    book.set_title('Python 3.13.2 Documentation')
    book.set_language('en')
    book.add_author('Python Software Foundation')

    # Map original URLs to EPUB filenames and titles
    url_to_filename = {}
    title_to_filename = {}
    epub_chapters = []
    for i, chapter in enumerate(chapters):
        filename = f'chap_{i+1}.xhtml'
        url_to_filename[chapter['url']] = filename
        title_to_filename[chapter['title']] = filename
        c = epub.EpubHtml(
            title=chapter['title'],
            file_name=filename,
            lang='en'
        )
        epub_chapters.append(c)
        book.add_item(c)

    # Fix internal links in content
    anchor_map = {
        'library-index': 'the-python-standard-library',
        'reference-index': 'the-python-language-reference',
        'extending-index': 'extending-and-embedding-the-python-interpreter',
        'c-api-index': 'python-c-api-reference-manual'
    }
    for i, chapter in enumerate(chapters):
        soup = BeautifulSoup(chapter['content'], 'html.parser')
        for link in soup.find_all('a', class_='reference internal'):
            if not isinstance(link, Tag):
                continue
            href = link.get('href')
            if href is None:
                continue
            href_str = str(href)
            if (
                not href_str or
                href_str.startswith(('http://', 'https://', 'mailto:'))
            ):
                continue
            if href_str.startswith('#'):
                continue
            if '#' in href_str:
                base, fragment = href_str.split('#', 1)
                fragment = '#' + fragment
            else:
                base, fragment = href_str, ''
            matching_url = (
                next((url for url in url_to_filename if base in url), None)
                or next(
                    (
                        url
                        for url in url_to_filename
                        if url.endswith(base.split('/')[-1])
                    ),
                    None,
                )
            )
            if fragment and fragment[1:] in anchor_map:
                fragment = '#' + anchor_map[fragment[1:]]
            if matching_url:
                link['href'] = url_to_filename[matching_url] + fragment
            elif href in chapter.get('internal_links', {}):
                target_title = chapter['internal_links'][href]
                for other_chap in chapters:
                    if other_chap['title'] == target_title:
                        link['href'] = (
                            url_to_filename[other_chap['url']] + fragment
                        )
                        break
                else:
                    print(
                        f"Unmapped link (title not found): {href} in "
                        f"{chapter['url']}"
                    )
            else:
                print(f"Unmapped link (no match): {href} in {chapter['url']}")
        epub_chapters[i].content = str(soup).encode('utf-8')
        ids = [
            tag.get('id')
            for tag in soup.find_all(id=True)
            if isinstance(tag, Tag)
        ]
        if not ids:
            print(f"Warning: No IDs found in {chapter['url']}")

    book.toc = epub_chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + epub_chapters

    epub_output = os.path.join("./outputs", "Python3Docs.epub")
    epub.write_epub(epub_output, book)
    print(f"EPUB created at: {epub_output}")


if __name__ == "__main__":
    create_ebook()
