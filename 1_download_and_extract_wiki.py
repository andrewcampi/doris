import os
import requests
import bz2
from tqdm import tqdm

def download_file(url, filename):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as file, tqdm(
        desc=filename,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as progress_bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            progress_bar.update(size)

def extract_bz2(filename, extract_path):
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)
    
    with bz2.BZ2File(filename) as bz_file:
        with open(os.path.join(extract_path, 'enwiki-latest-pages-articles-multistream.xml'), 'wb') as output_file:
            for data in iter(lambda: bz_file.read(100 * 1024 * 1024), b''):
                output_file.write(data)

def main():
    url = "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2"
    filename = "enwiki-latest-pages-articles-multistream.xml.bz2"
    extract_path = "wiki_raw"

    print("Downloading Wikipedia dump...")
    download_file(url, filename)
    
    print("Extracting Wikipedia dump...")
    extract_bz2(filename, extract_path)
    
    print("Removing packed download...")
    os.remove(filename)
    
    print("Process completed successfully.")

if __name__ == "__main__":
    main()