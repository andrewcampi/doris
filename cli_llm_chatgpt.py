import requests
import json
import urllib.parse
from langchain_openai import ChatOpenAI
from langchain.agents import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage
import os
from whoosh import index
from whoosh.qparser import QueryParser
from whoosh.highlight import ContextFragmenter, HtmlFormatter
from whoosh.analysis import StandardAnalyzer
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Book API function
def create_google_books_url(query, max_results=4):
    encoded_query = urllib.parse.quote(query.strip())
    base_url = "https://www.googleapis.com/books/v1/volumes"
    params = f"q={encoded_query}&maxResults={max_results}"
    if not encoded_query:
        params = f"q=*&maxResults={max_results}"
    return f"{base_url}?{params}"

@tool
def search_books(query: str) -> str:
    """Search for books using the Google Books API."""
    url = create_google_books_url(query)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'items' in data:
            books = data['items'][:3]
            results = []
            for book in books:
                title = book['volumeInfo'].get('title', 'Unknown Title')
                authors = book['volumeInfo'].get('authors', ['Unknown Author'])
                isbn = book['volumeInfo'].get('industryIdentifiers', [{}])[0].get('identifier', 'Unknown ISBN')
                results.append(f"{title} by {', '.join(authors)} - ISBN: {isbn}")
            return "\n".join(results)
    return "No books found or error occurred."

@tool
def get_factual_info(query: str) -> str:
    """Retrieve factual information about a given query."""
    title_index_dir = "wiki_title_index"
    title_ix = load_index(title_index_dir)

    # Search for relevant titles
    title_results = search_titles(query, title_ix, max_results=5)
    
    if not title_results:
        return f"No information found for '{query}'. Source: None"
    
    # Evaluate and choose the most relevant article
    chosen_article = choose_best_article(query, title_results)
    article_path = chosen_article['path']
    
    # Read the content of the chosen article
    with open(article_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # For now, return the first 100 characters of the content as a sample
    sample_content = content[:1000] + "..."
    
    return f"Information found in article: {chosen_article['title']}\n\nSample content:\n{sample_content}\n\nSource: {article_path}"

def load_index(index_dir):
    if not os.path.exists(index_dir):
        raise FileNotFoundError(f"Index directory '{index_dir}' not found. Please run the indexing script first.")
    return index.open_dir(index_dir)

def search_titles(query_str, ix, max_results=5):
    with ix.searcher() as searcher:
        query_parser = QueryParser("title", schema=ix.schema)
        query = query_parser.parse(query_str)
        results = searcher.search(query, limit=max_results)
        
        return [{"title": result["title"], "path": result["path"], "score": result.score} for result in results]

def choose_best_article(query, results):
    # Implement logic to choose the best article based on the query and results
    # This is a simple example; you may want to implement more sophisticated matching
    query_words = set(query.lower().split())
    
    best_match = None
    best_score = 0
    
    for result in results:
        title_words = set(result['title'].lower().split())
        match_score = len(query_words.intersection(title_words))
        
        if match_score > best_score or (match_score == best_score and result['score'] > best_match['score']):
            best_match = result
            best_score = match_score
    
    return best_match

# Set up the language model
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Define tools
tools = [search_books, get_factual_info]

# Update the system prompt
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

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

# Create the agent
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

# Create the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Main chat loop
def main():
    chat_history = []
    print("Welcome to the AI Assistant. Type 'quit' to exit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'quit':
            break
        
        result = agent_executor.invoke({"input": user_input, "chat_history": chat_history})
        print("\nAI:", result["output"])
        
        chat_history.extend([
            HumanMessage(content=user_input),
            AIMessage(content=result["output"]),
        ])

if __name__ == "__main__":
    main()
