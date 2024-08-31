import xml.parsers.expat
import re
import os
import html
from tqdm import tqdm
import io

def sanitize_filename(filename):
    # Existing sanitization
    sanitized = re.sub(r'[^\w\s-]', '', filename).strip().replace(' ', '_')
    
    # Limit filename length to 240 characters
    return sanitized[:240]

def get_subdirectory(filename):
    return filename[:2].lower() if len(filename) >= 2 else (filename[0].lower() if filename else '_')

def clean_and_convert_to_markdown(text):
    # Compile regex patterns once
    template_pattern = re.compile(r'{{[^}]+}}')
    cleanup_pattern = re.compile(r'<ref[^>]*>.*?</ref>|<!--.*?-->|\[\[Category:.*?\]\]|\[\[File:.*?\]\]|\[\[Image:.*?\]\]|\[http[^\]]+\]|<.*?>', re.DOTALL)
    bold_pattern = re.compile(r"'''(.*?)'''")
    italic_pattern = re.compile(r"''(.*?)''")
    heading_patterns = [
        (re.compile(r"==\s*(.*?)\s*=="), r"## \1"),
        (re.compile(r"===\s*(.*?)\s*==="), r"### \1"),
        (re.compile(r"====\s*(.*?)\s*===="), r"#### \1"),
    ]
    link_pattern = re.compile(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]')
    table_pattern = re.compile(r'{\|.*?\|}', re.DOTALL)
    whitespace_pattern = re.compile(r'^[\s*#:]+', re.MULTILINE)
    newline_pattern = re.compile(r'\n{3,}')
    
    text = template_pattern.sub('', text)
    text = cleanup_pattern.sub('', text)
    text = bold_pattern.sub(r"**\1**", text)
    text = italic_pattern.sub(r"*\1*", text)
    for pattern, repl in heading_patterns:
        text = pattern.sub(repl, text)
    text = link_pattern.sub(r'\1', text)
    text = table_pattern.sub('', text)
    text = whitespace_pattern.sub('', text)
    text = newline_pattern.sub('\n\n', text)
    
    # Remove everything from "References" or "See also" onwards
    text = re.split(r'^(References|See also)', text, flags=re.MULTILINE)[0]
    
    return text.strip()

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
                
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {html.unescape(title)}\n\n")
                    f.write(cleaned_text)

class WikiXmlHandler:
    def __init__(self):
        self.current_tag = []
        self.title = ""
        self.text = ""
        self.pages = []

    def start_element(self, name, attrs):
        self.current_tag.append(name)

    def end_element(self, name):
        if name == 'page':
            self.pages.append((self.title, self.text))
            self.title = ""
            self.text = ""
        self.current_tag.pop()

    def char_data(self, data):
        if self.current_tag[-1] == 'title':
            self.title += data
        elif self.current_tag[-1] == 'text':
            self.text += data

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