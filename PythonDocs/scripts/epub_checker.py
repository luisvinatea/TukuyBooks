"""ebup_checker.py
This script checks for broken links in an EPUB file.
It verifies that all internal links point to valid files and anchors within
the EPUB.
It also logs the results to a file and prints a summary.
Usage:
    python epub_checker.py <path_to_epub_file>
"""
import os
import logging
from datetime import datetime
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import bs4


def setup_logging(epub_file_path):
    """
    Set up logging configuration.
    Args:
        epub_file_path (str): Path to the EPUB file.
    Returns:
        str: Path to the log file.
    """
    # Create a log file in the same directory as the EPUB file
    log_dir = os.path.dirname(epub_file_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"epub_link_check_{timestamp}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
    )
    return log_file


def load_epub(epub_file_path):
    """
    Load an EPUB file.
    Args:
        epub_file_path (str): Path to the EPUB file.
    Returns:
        epub.EpubBook: Loaded EPUB book object or None if loading fails.
    """
    if not os.path.exists(epub_file_path):
        logging.error("Error: EPUB file not found at %s", epub_file_path)
        return None
    try:
        return epub.read_epub(epub_file_path)
    except (FileNotFoundError, epub.EpubException, RuntimeError) as e:
        logging.error("Error loading EPUB: %s", e)
        return None


def extract_valid_files_and_anchors(book):
    """
    Extract valid files and anchors from an EPUB book.
    Args:
        book (epub.EpubBook): EPUB book object.
    Returns:
        tuple: A set of valid files and a dictionary of file anchors.
    """
    valid_files = set()
    file_anchors = {}
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        filename = item.file_name.split('/')[-1]
        valid_files.add(filename)
        soup = BeautifulSoup(item.content, 'html.parser')
        anchors = set(
            tag.get('id')
            for tag in soup.find_all(True, id=True)
            if isinstance(tag, bs4.element.Tag) and tag.get('id')
        )
        file_anchors[filename] = anchors
    return valid_files, file_anchors


def parse_href(href, current_file):
    """
    Parse href into target_file and anchor, skip external or invalid links.
    """
    if not href:
        return None
    if isinstance(href, (list, tuple)):
        href = href[0]
    if not isinstance(href, str):
        return None
    if href.startswith(('http://', 'https://', 'mailto:')):
        return None
    if href.startswith('#'):
        target = current_file
        anchor = href[1:] if href != '#' else None
    else:
        parts = href.split('#', 1)
        target = parts[0].split('/')[-1]
        anchor = parts[1] if len(parts) == 2 else None
    return target, anchor


def classify_broken_link(target_file, anchor, valid_files, file_anchors):
    """
    Determine broken link issue or None if link is valid.
    """
    if target_file not in valid_files:
        return f"Target file '{target_file}' not found"
    if anchor and anchor not in file_anchors.get(target_file, set()):
        return f"Anchor '{anchor}' not found in '{target_file}'"
    return None


def find_broken_links(book, valid_files, file_anchors):
    """
    Find broken links in an EPUB book.
    Args:
        book (epub.EpubBook): EPUB book object.
        valid_files (set): Set of valid file names.
        file_anchors (dict): Dictionary of file anchors.
    Returns:
        tuple: A dictionary of broken links and
            the total count of broken links.
    """
    broken_links = {}
    total_broken = 0
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        filename = item.file_name.split('/')[-1]
        soup = BeautifulSoup(item.content, 'html.parser')
        for link in soup.find_all('a', href=True):
            if not isinstance(link, bs4.element.Tag):
                continue
            href = link.get('href')
            parsed = parse_href(href, filename)
            if not parsed:
                continue
            target, anchor = parsed
            issue = classify_broken_link(
                target,
                anchor,
                valid_files,
                file_anchors,
            )
            if not issue:
                continue
            total_broken += 1
            broken_links.setdefault(target, []).append({
                'source_file': filename,
                'link_text': link.get_text(strip=True) or 'No text',
                'original_href': href,
                'issue': issue
            })
    return broken_links, total_broken


def check_epub_links(epub_file_path):
    """
    Check for broken links in an EPUB file.
    Args:
        epub_file_path (str): Path to the EPUB file.
    Returns:
        dict: Summary of broken links and valid files.
    """
    book = load_epub(epub_file_path)
    if not book:
        return {
            'total_broken': 0,
            'broken_links': {},
            'valid_files': set(),
            'file_anchors': {},
        }
    valid_files, file_anchors = extract_valid_files_and_anchors(
        book
    )
    broken_links, total_broken = find_broken_links(
        book,
        valid_files,
        file_anchors,
    )
    log_file = setup_logging(epub_file_path)
    logging.info("\nEPUB Link Check Summary for: %s", epub_file_path)
    logging.info("Total chapters checked: %d", len(valid_files))
    logging.info("Total broken links found: %d", total_broken)
    if broken_links:
        logging.info("\nDetailed Report of Broken Links:")
        for target_file, issues in broken_links.items():
            logging.info("\nTarget File: '%s'", target_file)
            for issue in issues:
                logging.info("  - Source File: %s", issue['source_file'])
                logging.info("    Link Text: %s", issue['link_text'])
                logging.info("    Original href: %s", issue['original_href'])
                logging.info("    Issue: %s", issue['issue'])
    else:
        logging.info("\nNo broken links found! All links appear valid.")
    logging.info("\nReport saved to: %s", log_file)
    return {
        'total_broken': total_broken,
        'broken_links': broken_links,
        'valid_files': valid_files,
        'file_anchors': file_anchors,
    }


if __name__ == "__main__":

    epub_path = os.path.join("outputs", "Python3Docs.epub")
    check_epub_links(epub_path)
