import os  # Provides functions for interacting with the operating system
import shutil  # Provides functions for high-level file operations like copying and removing directories
from whoosh import index  # Provides functions for creating and managing search indexes
from whoosh.fields import Schema, TEXT, ID  # Provides classes for defining the schema of the index
from whoosh.analysis import StemmingAnalyzer  # Provides a stemming analyzer for text fields
from tqdm import tqdm  # Provides a progress bar for loops
import multiprocessing  # Provides support for concurrent execution using processes

# Function to create the schema for the index
def create_title_schema():
    return Schema(
        path=ID(stored=True),  # Store the file path
        title=TEXT(stored=True, analyzer=StemmingAnalyzer())  # Store the title with stemming analyzer
    )

# Function to process a single markdown file and extract its title
def process_file(file_path):
    if file_path.endswith('.md'):  # Check if the file is a markdown file
        with open(file_path, 'r', encoding='utf-8') as file:
            first_line = file.readline().strip()  # Read the first line
            if first_line.startswith('# '):  # Check if the first line is a markdown title
                title = first_line[2:]  # Extract the title text
                return file_path, title  # Return the file path and title
    return None  # Return None if the file is not a markdown file or has no title

# Function to create the title index
def create_title_index(root_dir, index_dir):
    if os.path.exists(index_dir):  # Check if the index directory exists
        shutil.rmtree(index_dir)  # Remove the existing index directory
    os.mkdir(index_dir)  # Create a new index directory
    
    schema = create_title_schema()  # Create the schema
    ix = index.create_in(index_dir, schema)  # Create the index

    all_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):  # Walk through the root directory
        all_files.extend(os.path.join(dirpath, filename) for filename in filenames if filename.endswith('.md'))  # Collect all markdown files

    num_processes = multiprocessing.cpu_count()  # Get the number of CPU cores
    pool = multiprocessing.Pool(processes=num_processes)  # Create a pool of worker processes

    writer = ix.writer()  # Create an index writer

    with tqdm(total=len(all_files), desc="Indexing titles") as pbar:  # Progress bar for indexing
        for result in pool.imap_unordered(process_file, all_files):  # Process files in parallel
            if result:  # If a valid result is returned
                file_path, title = result  # Unpack the result
                writer.add_document(path=file_path, title=title)  # Add the document to the index
                pbar.update(1)  # Update the progress bar
    
    print("Committing title index. This may take a while. Please wait...")
    writer.commit()  # Commit the changes to the index
    pool.close()  # Close the pool
    pool.join()  # Wait for all worker processes to finish

    return ix  # Return the index

# Main function to initiate the indexing process
def main():
    root_dir = "wiki/articles"  # Root directory containing the articles
    index_dir = "wiki_title_index"  # Directory to store the index

    print("Starting title indexing process...")
    try:
        index = create_title_index(root_dir, index_dir)  # Create the title index
        print(f"Title indexing complete. Index stored in '{index_dir}'")
        print("Success: Wiki title lookup system initiated successfully.")
    except Exception as e:  # Catch any exceptions
        print(f"Error: Failed to initiate wiki title lookup system. {str(e)}")
        return

# Entry point of the script
if __name__ == "__main__":
    main()
