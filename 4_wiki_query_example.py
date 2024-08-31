import os
import json
from whoosh import index
from whoosh.qparser import QueryParser
from whoosh.analysis import StandardAnalyzer

def load_index(index_dir):
    if not os.path.exists(index_dir):
        raise FileNotFoundError(f"Index directory '{index_dir}' not found. Please run the indexing script first.")
    return index.open_dir(index_dir)

def search_wiki(query_str, title_ix, max_results=5):
    analyzer = StandardAnalyzer()
    query_terms = [token.text for token in analyzer(query_str)]

    # Search for matching titles
    title_results = search_titles(query_str, title_ix, max_results)
    
    return {"results": title_results}

def search_titles(query_str, ix, max_results=7):
    with ix.searcher() as searcher:
        query_parser = QueryParser("title", schema=ix.schema)
        query = query_parser.parse(query_str)
        results = searcher.search(query, limit=max_results)
        
        return [{"title": result["title"], "path": result["path"], "score": result.score} for result in results]

def main():
    title_index_dir = "wiki_title_index"
    title_ix = load_index(title_index_dir)

    print(f"Title index directory: {title_index_dir}")
    print(f"Title index exists: {os.path.exists(title_index_dir)}")
    
    query = "Billy Joel"
    print(f"Searching for: {query}")
    results = search_wiki(query, title_ix)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()