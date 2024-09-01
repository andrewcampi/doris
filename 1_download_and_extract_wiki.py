import os  # For file and directory operations
import requests  # For downloading files from the web
import bz2  # For decompressing bz2 files
from tqdm import tqdm  # For displaying a progress bar during download

def download_file(url, filename):
    # Send a GET request to the URL, allowing streaming of the response content
    response = requests.get(url, stream=True)
    # Get the total size of the file from the response headers
    total_size = int(response.headers.get('content-length', 0))
    
    # Open the file in binary write mode and create a progress bar
    with open(filename, 'wb') as file, tqdm(
        desc=filename,  # Description for the progress bar
        total=total_size,  # Total size of the file for the progress bar
        unit='iB',  # Unit of measurement for the progress bar
        unit_scale=True,  # Scale the units (e.g., KB, MB)
        unit_divisor=1024,  # Divisor for scaling units
    ) as progress_bar:
        # Iterate over the response content in chunks
        for data in response.iter_content(chunk_size=1024):
            # Write each chunk to the file
            size = file.write(data)
            # Update the progress bar with the size of the written chunk
            progress_bar.update(size)

def extract_bz2(filename, extract_path):
    # Create the extraction directory if it doesn't exist
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)
    
    # Open the bz2 file for reading
    with bz2.BZ2File(filename) as bz_file:
        # Open the output file for writing
        with open(os.path.join(extract_path, 'enwiki-latest-pages-articles-multistream.xml'), 'wb') as output_file:
            # Read the bz2 file in chunks and write to the output file
            for data in iter(lambda: bz_file.read(100 * 1024 * 1024), b''):
                output_file.write(data)

def main():
    # URL of the Wikipedia dump
    url = "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2"
    # Filename for the downloaded bz2 file
    filename = "enwiki-latest-pages-articles-multistream.xml.bz2"
    # Directory to extract the contents of the bz2 file
    extract_path = "wiki_raw"

    print("Downloading Wikipedia dump...")
    # Download the Wikipedia dump
    download_file(url, filename)
    
    print("Extracting Wikipedia dump...")
    # Extract the downloaded bz2 file
    extract_bz2(filename, extract_path)
    
    print("Removing packed download...")
    # Remove the downloaded bz2 file after extraction
    os.remove(filename)
    
    print("Process completed successfully.")

if __name__ == "__main__":
    # Entry point of the script
    main()
