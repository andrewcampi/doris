import os
import shutil
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.analysis import StemmingAnalyzer
from tqdm import tqdm
import multiprocessing

def create_title_schema():
    return Schema(
        path=ID(stored=True),
        title=TEXT(stored=True, analyzer=StemmingAnalyzer())
    )

def process_file(file_path):
    if file_path.endswith('.md'):
        with open(file_path, 'r', encoding='utf-8') as file:
            first_line = file.readline().strip()
            if first_line.startswith('# '):
                title = first_line[2:]
                return file_path, title
    return None

def create_title_index(root_dir, index_dir):
    if os.path.exists(index_dir):
        shutil.rmtree(index_dir)
    os.mkdir(index_dir)
    
    schema = create_title_schema()
    ix = index.create_in(index_dir, schema)

    all_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        all_files.extend(os.path.join(dirpath, filename) for filename in filenames if filename.endswith('.md'))

    num_processes = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=num_processes)

    writer = ix.writer()

    with tqdm(total=len(all_files), desc="Indexing titles") as pbar:
        for result in pool.imap_unordered(process_file, all_files):
            if result:
                file_path, title = result
                writer.add_document(path=file_path, title=title)
                pbar.update(1)
    
    print("Committing title index. This may take a while. Please wait...")
    writer.commit()
    pool.close()
    pool.join()

    return ix

def main():
    root_dir = "wiki/articles"
    index_dir = "wiki_title_index"

    print("Starting title indexing process...")
    try:
        index = create_title_index(root_dir, index_dir)
        print(f"Title indexing complete. Index stored in '{index_dir}'")
        print("Success: Wiki title lookup system initiated successfully.")
    except Exception as e:
        print(f"Error: Failed to initiate wiki title lookup system. {str(e)}")
        return

if __name__ == "__main__":
    main()