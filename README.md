# Doris: A Showcase of AI Technologies

## Overview

Welcome to **Doris: A Showcase of AI Technologies**. This project demonstrates the integration of various AI and data processing technologies to create a powerful and interactive AI assistant. The key features of this project include:

1. **Reformatting and Indexing Wikipedia**: We reformat and index the entire Wikipedia dataset into a structure that is more accessible and understandable for AI models. This involves downloading, extracting, processing, and indexing Wikipedia articles.

2. **LangChain Agents**: We utilize LangChain agents to query the reformatted Wikipedia database and make API calls to retrieve book recommendations from Google Books. This ensures that the AI can provide accurate, up-to-date information, including ISBNs for books.

3. **Streamlit Frontend**: We showcase a simple yet visually appealing frontend using Streamlit. This allows users to interact with the AI assistant in a user-friendly manner.

## Using This Project

To get started with this project, follow these steps:

1. **Install Dependencies**:
   Run the following command to install all required dependencies:
   ```sh
   pip3 install -r requirements.txt
   ```

2. **Run the Scripts in Order**:
   The project consists of several scripts that need to be executed in a specific order. Here is the sequence:

   - **Step 1**: Download and extract the Wikipedia dump.
     ```sh
     python 1_download_and_extract_wiki.py
     ```

   - **Step 2**: Convert the extracted Wikipedia XML to a markdown structure.
     ```sh
     python 2_convert_wiki_xml_to_md_structure.py
     ```

   - **Step 3**: Index the Wikipedia article titles for efficient querying.
     ```sh
     python 3_index_wiki_article_titles.py
     ```

   - **Step 4**: Run the CLI-based AI assistant.
     ```sh
     python cli_llm_chatgpt.py
     ```

   - **Step 5**: Run the Streamlit-based AI assistant.
     ```sh
     streamlit run gui_streamlit.py
     ```

3. **Be Patient**:
   The process of downloading, reformatting, and indexing the entire Wikipedia dataset is time-consuming. Please be patient as it may take several hours to complete. We have employed Tqdm progress bars to display progress and estimate the time of completion for each step.

By following these steps, you will be able to explore the capabilities of Doris, our AI assistant, and see how it leverages advanced AI technologies to provide useful information and recommendations.
