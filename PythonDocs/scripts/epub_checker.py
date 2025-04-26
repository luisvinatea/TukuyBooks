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


def check_epub_links(epub_file_path):
    """
    Check for broken links in an EPUB file.
    Args:
        epub_file_path (str): Path to the EPUB file.
    Returns:
        dict: Summary of broken links and valid files.
    """
    if not os.path.exists(epub_file_path):
        logging.error("Error: EPUB file not found at %s", epub_file_path)
        return

    try:
        book = epub.read_epub(epub_file_path)
    except FileNotFoundError as e:
        logging.error("EPUB file not found: %s", e)
        return
    except epub.EpubException as e:
        logging.error("Error loading EPUB: %s", e)
        return
    except RuntimeError as e:
        logging.error("Unexpected error loading EPUB: %s", e)
        return

    # Collect valid files and anchors
    valid_files = set()
    file_anchors = {}
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        filename = item.file_name.split('/')[-1]
        valid_files.add(filename)
        soup = BeautifulSoup(item.content, 'html.parser')
        # Use .attrs.get() to access attributes safely
        anchors = set(
            tag.get('id')
            for tag in soup.find_all(True, id=True)
            if isinstance(tag, bs4.element.Tag) and tag.get('id') is not None
        )
        file_anchors[filename] = anchors

    # Check links
    broken_links = {}
    total_broken = 0

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        filename = item.file_name.split('/')[-1]
        soup = BeautifulSoup(item.content, 'html.parser')

        for link in soup.find_all('a', href=True):
            # Ensure link is a Tag and has 'href' attribute
            if not isinstance(link, bs4.element.Tag):
                continue
            href = link.get('href')
            if not href:
                continue
            # Ensure href is a string (sometimes it may be a list)
            if isinstance(href, (list, tuple)):
                href = href[0]
            # Add check to ensure href is a string now
            if not isinstance(href, str):
                continue
            if href.startswith(('http://', 'https://', 'mailto:')):
                continue

            # Split href into file and anchor
            if href.startswith('#'):
                # Fragment-only links point to the same file
                target_file = filename
                anchor = href[1:] if href != '#' else None
            elif '#' in href:
                target_file, anchor = href.split('#', 1)
                target_file = target_file.split('/')[-1]
            else:
                target_file = href.split('/')[-1]
                anchor = None

            # Check link validity
            if target_file == filename and anchor:  # Same-file anchor
                if anchor not in file_anchors.get(filename, set()):
                    total_broken += 1
                    broken_links.setdefault(target_file, []).append({
                        'source_file': filename,
                        'link_text': link.get_text(strip=True) or 'No text',
                        'original_href': href,
                        'issue': f"Anchor '{anchor}' not found in '{filename}'"
                    })
            elif target_file not in valid_files:  # Non-existent file
                total_broken += 1
                broken_links.setdefault(target_file, []).append({
                    'source_file': filename,
                    'link_text': link.get_text(strip=True) or 'No text',
                    'original_href': href,
                    'issue': f"Target file '{target_file}' not found"
                })
            elif (
                anchor and
                anchor not in file_anchors.get(target_file, set())
            ):  # Missing anchor in target file
                total_broken += 1
                broken_links.setdefault(target_file, []).append({
                    'source_file': filename,
                    'link_text': link.get_text(strip=True) or 'No text',
                    'original_href': href,
                    'issue': f"Anchor '{anchor}' not found in '{target_file}'"
                })

    # Log results
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
        'file_anchors': file_anchors
    }


if __name__ == "__main__":

    epub_path = os.path.join("outputs", "Python3Docs.epub")
    check_epub_links(epub_path)
