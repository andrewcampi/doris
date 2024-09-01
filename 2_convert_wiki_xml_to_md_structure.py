import xml.parsers.expat  # For parsing XML data efficiently
import re  # For using regular expressions to clean and convert text
import os  # For file and directory operations
import html  # For unescaping HTML entities in text
from tqdm import tqdm  # For displaying a progress bar during processing
import io  # For handling input and output operations

# Function to sanitize filenames by removing invalid characters and limiting length
def sanitize_filename(filename):
    sanitized = re.sub(r'[^\w\s-]', '', filename).strip().replace(' ', '_')
    return sanitized[:240]

# Function to determine subdirectory based on the first two characters of the filename
def get_subdirectory(filename):
    return filename[:2].lower() if len(filename) >= 2 else (filename[0].lower() if filename else '_')

# Function to clean and convert wiki text to markdown format
def clean_and_convert_to_markdown(text):
    # Compile regex patterns once for efficiency
    template_pattern = re.compile(r'{{[^}]+}}')  # Matches and removes template tags like {{...}}
    cleanup_pattern = re.compile(r'<ref[^>]*>.*?</ref>|<!--.*?-->|\[\[Category:.*?\]\]|\[\[File:.*?\]\]|\[\[Image:.*?\]\]|\[http[^\]]+\]|<.*?>', re.DOTALL)  # Matches and removes references, comments, categories, files, images, external links, and HTML tags
    bold_pattern = re.compile(r"'''(.*?)'''")  # Matches and converts bold text '''...''' to markdown bold **...**
    italic_pattern = re.compile(r"''(.*?)''")  # Matches and converts italic text ''...'' to markdown italic *...*
    heading_patterns = [
        (re.compile(r"==\s*(.*?)\s*=="), r"## \1"),  # Matches and converts level 2 headings ==...== to markdown ## ...
        (re.compile(r"===\s*(.*?)\s*==="), r"### \1"),  # Matches and converts level 3 headings ===...=== to markdown ### ...
        (re.compile(r"====\s*(.*?)\s*===="), r"#### \1"),  # Matches and converts level 4 headings ====...==== to markdown #### ...
    ]
    link_pattern = re.compile(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]')  # Matches and converts internal links [[...|...]] or [[...]] to just the link text
    table_pattern = re.compile(r'{\|.*?\|}', re.DOTALL)  # Matches and removes table markup
    whitespace_pattern = re.compile(r'^[\s*#:]+', re.MULTILINE)  # Matches and removes leading whitespace, asterisks, colons, and hash symbols at the beginning of lines
    newline_pattern = re.compile(r'\n{3,}')  # Matches and reduces multiple consecutive newlines to two newlines
    
    # Apply regex patterns to clean the text
    text = template_pattern.sub('', text)  # Remove template tags
    text = cleanup_pattern.sub('', text)  # Remove references, comments, categories, files, images, external links, and HTML tags
    text = bold_pattern.sub(r"**\1**", text)  # Convert bold text to markdown bold
    text = italic_pattern.sub(r"*\1*", text)  # Convert italic text to markdown italic
    for pattern, repl in heading_patterns:
        text = pattern.sub(repl, text)  # Convert headings to markdown headings
    text = link_pattern.sub(r'\1', text)  # Convert internal links to plain text
    text = table_pattern.sub('', text)  # Remove table markup
    text = whitespace_pattern.sub('', text)  # Remove leading whitespace, asterisks, colons, and hash symbols
    text = newline_pattern.sub('\n\n', text)  # Reduce multiple consecutive newlines to two newlines
    
    # Remove everything from "References" or "See also" onwards
    text = re.split(r'^(References|See also)', text, flags=re.MULTILINE)[0]
    
    return text.strip()

# Function to process each wiki page
def process_page(title, text):
    if title and text:
        filename = sanitize_filename(title)
        cleaned_text = clean_and_convert_to_markdown(text)
        if cleaned_text.strip():
            lines = cleaned_text.split('\n', 4)
            if len(lines) >= 4 and 'REDIRECT' not in lines[3]:
                subdirectory = get_subdirectory(filename)
                directory = f"wiki/articles/{subdirectory}"
                os.makedirs(directory, exist_ok=True)
                full_path = f"{directory}/{filename}.md"
                
                # Check if the full path exceeds the maximum allowed length
                if len(full_path.encode('utf-8')) > 255:
                    # If it does, truncate the filename further
                    excess = len(full_path.encode('utf-8')) - 255
                    filename = filename[:-excess-3] + "..."
                    full_path = f"{directory}/{filename}.md"
                
                # Write the cleaned text to a markdown file
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {html.unescape(title)}\n\n")
                    f.write(cleaned_text)

# Class to handle XML parsing events
class WikiXmlHandler:
    def __init__(self):
        self.current_tag = []
        self.title = ""
        self.text = ""
        self.pages = []

    # Called when an XML element starts
    def start_element(self, name, attrs):
        self.current_tag.append(name)

    # Called when an XML element ends
    def end_element(self, name):
        if name == 'page':
            self.pages.append((self.title, self.text))
            self.title = ""
            self.text = ""
        self.current_tag.pop()

    # Called when character data is encountered
    def char_data(self, data):
        if self.current_tag[-1] == 'title':
            self.title += data
        elif self.current_tag[-1] == 'text':
            self.text += data

# Function to process the entire Wikipedia dump file
def process_wiki_dump(file_path):
    chunk_size = 50 * 1024 * 1024  # 50 MB chunks
    file_size = os.path.getsize(file_path)
    
    with open(file_path, 'rb') as file, \
         tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024, desc="Processing Wikipedia dump") as pbar:
        
        parser = xml.parsers.expat.ParserCreate()
        handler = WikiXmlHandler()
        parser.StartElementHandler = handler.start_element
        parser.EndElementHandler = handler.end_element
        parser.CharacterDataHandler = handler.char_data
        
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            parser.Parse(chunk)
            for title, text in handler.pages:
                process_page(title, text)
            handler.pages.clear()
            pbar.update(len(chunk))

# Main function to start the processing
def main():
    try:
        xml_file = "wiki_raw/enwiki-latest-pages-articles-multistream.xml"
        os.makedirs("wiki/articles", exist_ok=True)

        print("Starting Wikipedia dump processing...")
        process_wiki_dump(xml_file)
        print("\nConversion complete!")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
