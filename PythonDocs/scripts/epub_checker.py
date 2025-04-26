import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re
import os
import logging
from datetime import datetime

def setup_logging(epub_path):
    log_dir = os.path.dirname(epub_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"epub_link_check_{timestamp}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
    )
    return log_file

def check_epub_links(epub_path):
    if not os.path.exists(epub_path):
        logging.error(f"Error: EPUB file not found at {epub_path}")
        return

    try:
        book = epub.read_epub(epub_path)
    except Exception as e:
        logging.error(f"Error loading EPUB: {e}")
        return

    # Collect valid files and anchors
    valid_files = set()
    file_anchors = {}
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        filename = item.file_name.split('/')[-1]
        valid_files.add(filename)
        soup = BeautifulSoup(item.content, 'html.parser')
        anchors = set(tag['id'] for tag in soup.find_all(id=True))
        file_anchors[filename] = anchors

    # Check links
    broken_links = {}
    total_broken = 0
    
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        filename = item.file_name.split('/')[-1]
        soup = BeautifulSoup(item.content, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith(('http://', 'https://', 'mailto:')):
                continue
            
            # Split href into file and anchor
            if href.startswith('#'):
                target_file = filename  # Fragment-only links point to the same file
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
            elif anchor and anchor not in file_anchors.get(target_file, set()):  # Missing anchor in target file
                total_broken += 1
                broken_links.setdefault(target_file, []).append({
                    'source_file': filename,
                    'link_text': link.get_text(strip=True) or 'No text',
                    'original_href': href,
                    'issue': f"Anchor '{anchor}' not found in '{target_file}'"
                })

    # Log results
    log_file = setup_logging(epub_path)
    logging.info(f"\nEPUB Link Check Summary for: {epub_path}")
    logging.info(f"Total chapters checked: {len(valid_files)}")
    logging.info(f"Total broken links found: {total_broken}")
    
    if broken_links:
        logging.info("\nDetailed Report of Broken Links:")
        for target_file, issues in broken_links.items():
            logging.info(f"\nTarget File: '{target_file}'")
            for issue in issues:
                logging.info(f"  - Source File: {issue['source_file']}")
                logging.info(f"    Link Text: {issue['link_text']}")
                logging.info(f"    Original href: {issue['original_href']}")
                logging.info(f"    Issue: {issue['issue']}")
    else:
        logging.info("\nNo broken links found! All links appear valid.")
    
    logging.info(f"\nReport saved to: {log_file}")

    return {
        'total_broken': total_broken,
        'broken_links': broken_links,
        'valid_files': valid_files,
        'file_anchors': file_anchors
    }

if __name__ == "__main__":
    epub_path = "/home/luisvinatea/Dev/Repos/ScrapingProjects/ByteBooks/PythonDocs/outputs/Python3Docs.epub"
    check_epub_links(epub_path)