import os  # Provides functions to interact with the operating system, such as checking if a directory exists
import json  # Provides functions to work with JSON data, such as converting Python objects to JSON strings
from whoosh import index  # Provides functions to create, open, and manage search indexes
from whoosh.qparser import QueryParser  # Provides functions to parse query strings into query objects
from whoosh.analysis import StandardAnalyzer  # Provides functions to tokenize text into individual terms for indexing and searching

# Function to load the index from the specified directory
def load_index(index_dir):
    # Check if the index directory exists
    if not os.path.exists(index_dir):
        # Raise an error if the directory does not exist
        raise FileNotFoundError(f"Index directory '{index_dir}' not found. Please run the indexing script first.")
    # Open and return the index
    return index.open_dir(index_dir)

# Function to search the wiki using a query string
def search_wiki(query_str, title_ix, max_results=5):
    # Initialize the analyzer to tokenize the query string
    analyzer = StandardAnalyzer()
    # Tokenize the query string into individual terms
    query_terms = [token.text for token in analyzer(query_str)]

    # Search for matching titles in the index
    title_results = search_titles(query_str, title_ix, max_results)
    
    # Return the search results as a dictionary
    return {"results": title_results}

# Function to search for titles in the index
def search_titles(query_str, ix, max_results=7):
    # Open a searcher for the index
    with ix.searcher() as searcher:
        # Initialize the query parser for the "title" field
        query_parser = QueryParser("title", schema=ix.schema)
        # Parse the query string into a query object
        query = query_parser.parse(query_str)
        # Search the index for matching titles, limiting the results
        results = searcher.search(query, limit=max_results)
        
        # Return the search results as a list of dictionaries
        return [{"title": result["title"], "path": result["path"], "score": result.score} for result in results]

# Main function to execute the script
def main():
    # Directory where the title index is stored
    title_index_dir = "wiki_title_index"
    # Load the title index from the directory
    title_ix = load_index(title_index_dir)

    # Print the directory and existence status of the title index
    print(f"Title index directory: {title_index_dir}")
    print(f"Title index exists: {os.path.exists(title_index_dir)}")
    
    # Query string to search for
    query = "Billy Joel"
    # Print the query string
    print(f"Searching for: {query}")
    # Perform the search and get the results
    results = search_wiki(query, title_ix)
    # Print the search results in JSON format
    print(json.dumps(results, indent=2))

# Entry point of the script
if __name__ == "__main__":
    main()
