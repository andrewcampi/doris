import streamlit as st  # For creating the web app interface
import requests  # For making HTTP requests to external APIs
import json  # For handling JSON data
import urllib.parse  # For URL encoding
from langchain_openai import ChatOpenAI  # For interacting with OpenAI's language model
from langchain.agents import tool  # For defining tools that the agent can use
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # For creating and managing chat prompts
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages  # For formatting messages for OpenAI tools
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser  # For parsing the output from OpenAI tools
from langchain.agents import AgentExecutor  # For executing the agent with the defined tools
from langchain_core.messages import AIMessage, HumanMessage  # For handling AI and human messages
import os  # For interacting with the operating system
from whoosh import index  # For working with the Whoosh search index
from whoosh.qparser import QueryParser  # For parsing search queries
from dotenv import load_dotenv  # For loading environment variables from a .env file

# Load environment variables from a .env file
load_dotenv()

# Function to create a Google Books API URL based on a search query
def create_google_books_url(query, max_results=4):
    encoded_query = urllib.parse.quote(query.strip())  # URL encode the query
    base_url = "https://www.googleapis.com/books/v1/volumes"
    params = f"q={encoded_query}&maxResults={max_results}"  # Set query parameters
    if not encoded_query:
        params = f"q=*&maxResults={max_results}"  # Default to all results if query is empty
    return f"{base_url}?{params}"

# Tool to search for books using the Google Books API
@tool
def search_books(query: str) -> str:
    """Search for books using the Google Books API."""
    url = create_google_books_url(query)  # Create the API URL
    response = requests.get(url)  # Make the HTTP request
    if response.status_code == 200:  # Check if the request was successful
        data = response.json()  # Parse the JSON response
        if 'items' in data:
            books = data['items'][:3]  # Get the first 3 books
            results = []
            for book in books:
                title = book['volumeInfo'].get('title', 'Unknown Title')  # Get the book title
                authors = book['volumeInfo'].get('authors', ['Unknown Author'])  # Get the book authors
                isbn = book['volumeInfo'].get('industryIdentifiers', [{}])[0].get('identifier', 'Unknown ISBN')  # Get the ISBN
                results.append(f"{title} by {', '.join(authors)} - ISBN: {isbn}")  # Format the result
            return "\n".join(results)  # Join results with newlines
    return "No books found or error occurred."  # Return error message if no books found

# Tool to retrieve factual information from a local Wikipedia index
@tool
def get_factual_info(query: str) -> str:
    """Retrieve factual information about a given query."""
    title_index_dir = "wiki_title_index"  # Directory where the index is stored
    title_ix = load_index(title_index_dir)  # Load the index

    # Search for relevant titles in the index
    title_results = search_titles(query, title_ix, max_results=5)
    
    if not title_results:
        return f"No information found for '{query}'. Source: None"  # Return if no results found
    
    # Evaluate and choose the most relevant article
    chosen_article = choose_best_article(query, title_results)
    article_path = chosen_article['path']  # Get the path of the chosen article
    
    # Read the content of the chosen article
    with open(article_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Return the first 1000 characters of the content
    sample_content = content[:1000] + "..."
    
    return f"Information found in article: {chosen_article['title']}\n\nSample content:\n{sample_content}\n\nSource: {article_path}"

# Function to load the search index
def load_index(index_dir):
    if not os.path.exists(index_dir):  # Check if the index directory exists
        st.error(f"Index directory '{index_dir}' not found. Please run the indexing script first.")  # Show error if not found
        return None
    return index.open_dir(index_dir)  # Open the index directory

# Function to search for titles in the index
def search_titles(query_str, ix, max_results=5):
    with ix.searcher() as searcher:  # Open a searcher
        query_parser = QueryParser("title", schema=ix.schema)  # Create a query parser for the title field
        query = query_parser.parse(query_str)  # Parse the query string
        results = searcher.search(query, limit=max_results)  # Search the index

        # Return the search results
        return [{"title": result["title"], "path": result["path"], "score": result.score} for result in results]

# Function to choose the best article based on the query
def choose_best_article(query, results):
    query_words = set(query.lower().split())  # Split the query into words
    
    best_match = None
    best_score = 0
    
    for result in results:
        title_words = set(result['title'].lower().split())  # Split the title into words
        match_score = len(query_words.intersection(title_words))  # Calculate the match score
        
        # Choose the result with the highest match score or highest search score
        if match_score > best_score or (match_score == best_score and result['score'] > best_match['score']):
            best_match = result
            best_score = match_score
    
    return best_match

# Streamlit UI setup
st.title("AI Librarian Assistant")  # Set the title of the app

# Sidebar for API key input
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")  # Input for API key

if api_key:
    # Set up the language model with the provided API key
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)

    # Define the tools that the agent can use
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

        Use the appropriate tool based on the user's query. You do not have the ability to answer questions about current events or the internet. Always provide the source of your information as the file path, not a URL. If you couldn't find a source but attempted to search, state 'Source: None'."""),
        MessagesPlaceholder(variable_name=MEMORY_KEY),  # Placeholder for chat history
        ("user", "{input}"),  # Placeholder for user input
        MessagesPlaceholder(variable_name="agent_scratchpad"),  # Placeholder for intermediate steps
    ])

    # Bind tools to the language model
    llm_with_tools = llm.bind_tools(tools)

    # Create the agent with the defined tools and prompt
    agent = (
        {
            "input": lambda x: x["input"],  # Extract input from the user
            "agent_scratchpad": lambda x: format_to_openai_tool_messages(x["intermediate_steps"]),  # Format intermediate steps
            "chat_history": lambda x: x["chat_history"],  # Extract chat history
        }
        | prompt
        | llm_with_tools
        | OpenAIToolsAgentOutputParser()  # Parse the output from the tools
    )

    # Create the agent executor
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    prompt = st.chat_input("Hello! What can I do for you today?")
    if prompt:
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        st.spinner("Finding the best books...")  # Show a spinner while processing

        with st.chat_message("assistant"):
            # Invoke the agent executor with the user input and chat history
            response = agent_executor.invoke(
                {
                    "input": prompt,
                    "chat_history": st.session_state.messages,
                }
            )
            
            st.markdown(response["output"])  # Display the assistant's response
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response["output"]})

else:
    st.warning("Please enter your OpenAI API key in the sidebar to start the conversation.")  # Show warning if API key is not provided
