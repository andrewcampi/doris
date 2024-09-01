import requests  # For making HTTP requests to external APIs
import json  # For parsing JSON responses from APIs
import urllib.parse  # For encoding URLs
from langchain_openai import ChatOpenAI  # For interacting with the OpenAI language model
from langchain.agents import tool  # For defining tools that the language model can use
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # For creating chat prompts and placeholders
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages  # For formatting intermediate steps for OpenAI tools
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser  # For parsing the output from OpenAI tools
from langchain.agents import AgentExecutor  # For executing the agent with tools
from langchain_core.messages import AIMessage, HumanMessage  # For handling AI and human messages
import os  # For interacting with the operating system, such as reading environment variables
from whoosh import index  # For working with the Whoosh search index
from whoosh.qparser import QueryParser  # For parsing search queries
from whoosh.highlight import ContextFragmenter, HtmlFormatter  # For highlighting search results
from whoosh.analysis import StandardAnalyzer  # For analyzing text in the search index
from dotenv import load_dotenv  # For loading environment variables from a .env file

# Load environment variables from .env file
load_dotenv()

# Function to create a Google Books API URL based on a search query
def create_google_books_url(query, max_results=4):
    encoded_query = urllib.parse.quote(query.strip())  # Encode the query for URL
    base_url = "https://www.googleapis.com/books/v1/volumes"
    params = f"q={encoded_query}&maxResults={max_results}"  # Set query parameters
    if not encoded_query:
        params = f"q=*&maxResults={max_results}"  # Default to all results if query is empty
    return f"{base_url}?{params}"

# Define a tool for searching books using the Google Books API
@tool
def search_books(query: str) -> str:
    """Search for books using the Google Books API."""
    url = create_google_books_url(query)  # Create the API URL
    response = requests.get(url)  # Make the API request
    if response.status_code == 200:
        data = response.json()  # Parse the JSON response
        if 'items' in data:
            books = data['items'][:3]  # Get the top 3 books
            results = []
            for book in books:
                title = book['volumeInfo'].get('title', 'Unknown Title')  # Get book title
                authors = book['volumeInfo'].get('authors', ['Unknown Author'])  # Get book authors
                isbn = book['volumeInfo'].get('industryIdentifiers', [{}])[0].get('identifier', 'Unknown ISBN')  # Get book ISBN
                results.append(f"{title} by {', '.join(authors)} - ISBN: {isbn}")  # Format the result
            return "\n".join(results)  # Return formatted results
    return "No books found or error occurred."  # Handle errors or no results

# Define a tool for retrieving factual information from a local Wikipedia index
@tool
def get_factual_info(query: str) -> str:
    """Retrieve factual information about a given query."""
    title_index_dir = "wiki_title_index"  # Directory of the title index
    title_ix = load_index(title_index_dir)  # Load the index

    # Search for relevant titles in the index
    title_results = search_titles(query, title_ix, max_results=5)
    
    if not title_results:
        return f"No information found for '{query}'. Source: None"  # Handle no results
    
    # Choose the most relevant article from the search results
    chosen_article = choose_best_article(query, title_results)
    article_path = chosen_article['path']  # Get the path of the chosen article
    
    # Read the content of the chosen article
    with open(article_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Return a sample of the content
    sample_content = content[:1000] + "..."
    
    return f"Information found in article: {chosen_article['title']}\n\nSample content:\n{sample_content}\n\nSource: {article_path}"

# Function to load the index from a directory
def load_index(index_dir):
    if not os.path.exists(index_dir):
        raise FileNotFoundError(f"Index directory '{index_dir}' not found. Please run the indexing script first.")
    return index.open_dir(index_dir)

# Function to search titles in the index
def search_titles(query_str, ix, max_results=5):
    with ix.searcher() as searcher:
        query_parser = QueryParser("title", schema=ix.schema)  # Create a query parser
        query = query_parser.parse(query_str)  # Parse the query string
        results = searcher.search(query, limit=max_results)  # Search the index
        
        # Format the search results
        return [{"title": result["title"], "path": result["path"], "score": result.score} for result in results]

# Function to choose the best article from search results
def choose_best_article(query, results):
    query_words = set(query.lower().split())  # Split query into words
    
    best_match = None
    best_score = 0
    
    for result in results:
        title_words = set(result['title'].lower().split())  # Split title into words
        match_score = len(query_words.intersection(title_words))  # Calculate match score
        
        # Choose the best match based on score
        if match_score > best_score or (match_score == best_score and result['score'] > best_match['score']):
            best_match = result
            best_score = match_score
    
    return best_match

# Set up the language model with specific parameters
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Define the tools to be used by the language model
tools = [search_books, get_factual_info]

# Update the system prompt with instructions for the AI
MEMORY_KEY = "chat_history"
prompt = ChatPromptTemplate.from_messages([
    ("system", """Your name is 'Doris'. You are a helpful AI librarian. You are very smart, capable of searching for books and retrieving factual information by using your 'Wikipedia'.

    When using the get_factual_info tool:
    1. Always use broad, general queries that match potential article titles.
    2. For questions about people, use just their name.
    3. For questions about places or events, use the main subject without specific details.
    4. Avoid including question words or phrases in your query.

    Examples:
    - For "Where was Thomas Jefferson born?", query "Thomas Jefferson"
    - For "What year did World War II end?", query "World War II"
    - For "Who invented the telephone?", query "Telephone" or "Alexander Graham Bell"

    Use the appropriate tool based on the user's query. Always provide the source of your information as the file path, not a URL. If you could not find the information, attempt to answer the question yourself, but say at the end 'Source: None'."""),
    MessagesPlaceholder(variable_name=MEMORY_KEY),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Bind the tools to the language model
llm_with_tools = llm.bind_tools(tools)

# Create the agent with input, prompt, tools, and output parser
agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(x["intermediate_steps"]),
        "chat_history": lambda x: x["chat_history"],
    }
    | prompt
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)

# Create the agent executor to handle the agent and tools
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Main chat loop to interact with the user
def main():
    chat_history = []  # Initialize chat history
    print("Welcome to the AI Assistant. Type 'quit' to exit.")
    while True:
        user_input = input("\nYou: ")  # Get user input
        if user_input.lower() == 'quit':
            break
        
        # Invoke the agent executor with user input and chat history
        result = agent_executor.invoke({"input": user_input, "chat_history": chat_history})
        print("\nAI:", result["output"])  # Print the AI's response
        
        # Update chat history with user and AI messages
        chat_history.extend([
            HumanMessage(content=user_input),
            AIMessage(content=result["output"]),
        ])

# Run the main function if the script is executed directly
if __name__ == "__main__":
    main()
