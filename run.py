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

BASE_URL = args.url
DOWNLOAD_DIR = args.output
DOWNLOADABLE_FILE_EXTENSIONS = ('.zip', '.rar', '.7z', '.tar.gz', '.tar', '.gz', '.docx', '.pdf') 

crawled = []

def is_file_downloadable(url):
    return url.lower().endswith(DOWNLOADABLE_FILE_EXTENSIONS)

def get_relative_url(full_url, base_url):
    parsed_base = urlparse(base_url)
    parsed_full = urlparse(full_url)

    if parsed_base.netloc != parsed_full.netloc:
        return parsed_full.path.lstrip('/')

    base_path = parsed_base.path
    full_path = parsed_full.path

    if full_path.startswith(base_path):
        return full_path[len(base_path):].lstrip('/')
    return full_path.lstrip('/')


def download_file(file_url):
    filename = get_relative_url(file_url, BASE_URL)
    save_path = os.path.join(DOWNLOAD_DIR, filename)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    downloaded_size = 0
    if os.path.exists(save_path):
        downloaded_size = os.path.getsize(save_path)
    
    
    headers = {'Range': f'bytes={downloaded_size}-'}
    with requests.get(file_url, auth=auth, headers=headers, stream=True) as response:
        if response.status_code == 416:
            print(f'{filename} already fully downloaded.')
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

        print(f'${filename} saved to: {save_path}')

def crawl_directory(url):
    if url in crawled:
        return
    
    crawled.append(url)

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
        crawl_directory(BASE_URL)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
        sys.exit(1)
