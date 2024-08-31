import os
import shutil
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.analysis import StemmingAnalyzer
from tqdm import tqdm
import multiprocessing

def create_schema():
    return Schema(
        path=ID(stored=True),
        content=TEXT(analyzer=StemmingAnalyzer())
    )

def process_file(file_path):
    if file_path.endswith('.md'):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return file_path, content
    return None

def create_index(root_dir, index_dir):
    if os.path.exists(index_dir):
        shutil.rmtree(index_dir)
    os.mkdir(index_dir)
    
    schema = create_schema()
    ix = index.create_in(index_dir, schema)

    all_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        all_files.extend(os.path.join(dirpath, filename) for filename in filenames if filename.endswith('.md'))

    num_processes = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=num_processes)

    writer = ix.writer()

    with tqdm(total=len(all_files), desc="Indexing files") as pbar:
        for result in pool.imap_unordered(process_file, all_files):
            if result:
                file_path, content = result
                writer.add_document(path=file_path, content=content)
                pbar.update(1)
    
    print("Committing index. This will likely take as long as the previous step. Please wait...")
    writer.commit()
    pool.close()
    pool.join()

    return ix

def main():
    root_dir = "wiki/articles"
    index_dir = "wiki_index"

    print("Starting indexing process...")
    try:
        index = create_index(root_dir, index_dir)
        print(f"Indexing complete. Index stored in '{index_dir}'")
        print("Success: Wiki lookup system initiated successfully.")
    except Exception as e:
        print(f"Error: Failed to initiate wiki lookup system. {str(e)}")
        return

if __name__ == "__main__":
    main()