import os
import sys
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm

# Configuration

parser = argparse.ArgumentParser(description="Download compressed files from an Apache web directory using Basic Auth.")
parser.add_argument('--url', required=True, help='Base URL of the Apache web server (e.g., http://localhost/)')
parser.add_argument('--username', required=True, help='Username for Basic Auth')
parser.add_argument('--password', required=True, help='Password for Basic Auth')
parser.add_argument('--output', default='downloaded/', help='Directory to save downloaded .zip files')
args = parser.parse_args()

auth = (args.username, args.password)

DOWNLOAD_DIR = args.output
DOWNLOADABLE_FILE_EXTENSIONS = ('.zip', '.rar', '.7z', '.tar.gz', '.tar', '.gz') 

crawled = {}

def ensure_download_dir():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

def is_file_downloadable(url):
    return url.lower().endswith(DOWNLOADABLE_FILE_EXTENSIONS)

def download_file(zip_url):
    filename = os.path.basename(urlparse(zip_url).path)
    save_path = os.path.join(DOWNLOAD_DIR, filename)

    downloaded_size = 0
    if os.path.exists(save_path):
        downloaded_size = os.path.getsize(save_path)
    
    
    headers = {'Range': f'bytes={downloaded_size}-'}
    with requests.get(zip_url, auth=auth, headers=headers, stream=True) as response:
        if response.status_code == 416:
            print(f'{zip_url} already fully downloaded.')
            return
        
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0)) + downloaded_size
        mode = 'ab' if downloaded_size else 'wb'

        with open(save_path, mode) as f, tqdm(
                initial=downloaded_size,
                total=total_size, unit='B', unit_scale=True, desc=filename
            ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))

        print(f'${zip_url} saved to: {save_path}')

def crawl_directory(url):
    if url in crawled:
        return
    
    crawled[url] = True

    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            full_url = urljoin(url, href)
            if is_file_downloadable(href):
                download_file(full_url)
            elif href.endswith('/') and href != '../':
                crawl_directory(full_url)
    except Exception as e:
        print(f'Error accessing {url}: {e}')

if __name__ == '__main__':
    try:
        ensure_download_dir()
        crawl_directory(args.url)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
        sys.exit(1)
