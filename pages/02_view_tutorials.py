import streamlit as st
import os
import glob
import re
from pathlib import Path
import markdown
import base64

# Set page config
st.set_page_config(
    page_title="View Tutorials",
    page_icon="📚",
    layout="wide"
)

# Title
st.title("📚 Tutorial Browser")
st.markdown("Browse and view generated tutorials from the output directory.")

# Function to get all project directories in the output folder
def get_project_directories(base_path="output"):
    if not os.path.exists(base_path):
        return []
    
    directories = [d for d in os.listdir(base_path) 
                  if os.path.isdir(os.path.join(base_path, d))]
    return sorted(directories)

# Function to get all markdown files in a directory
def get_markdown_files(project_dir):
    md_files = []
    
    # Check for index.md first
    index_path = os.path.join("output", project_dir, "index.md")
    if os.path.exists(index_path):
        md_files.append(("📌 Index", index_path))
    
    # Get all other markdown files
    pattern = os.path.join("output", project_dir, "*.md")
    for file_path in glob.glob(pattern):
        if file_path.endswith("index.md"):
            continue  # Skip index.md as it's already handled
        
        # Extract chapter number from filename if possible
        filename = os.path.basename(file_path)
        match = re.match(r"(\d+)_(.+)\.md", filename)
        if match:
            chapter_num = int(match.group(1))
            chapter_name = match.group(2).replace("_", " ").title()
            display_name = f"Chapter {chapter_num}: {chapter_name}"
        else:
            display_name = filename
        
        md_files.append((display_name, file_path))
    
    # Sort by chapter number if it exists
    def sort_key(item):
        match = re.match(r"Chapter (\d+)", item[0])
        if match:
            return int(match.group(1))
        return float('inf')  # Put non-chapter files at the end
    
    return sorted(md_files, key=sort_key)

# Function to read markdown file content
def read_markdown_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# Function to convert markdown diagrams to HTML
def convert_markdown_to_html(markdown_text):
    # Convert markdown to HTML
    html = markdown.markdown(markdown_text, extensions=['fenced_code', 'tables'])
    
    # Add support for Mermaid diagrams
    if "```mermaid" in markdown_text:
        html += """
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>
        mermaid.initialize({startOnLoad:true});
        </script>
        """
        html = html.replace('<pre><code class="mermaid">', '<div class="mermaid">')
        html = html.replace('</code></pre>', '</div>')
    
    return html

# Function to create download link for a file
def get_download_link(file_path, link_text="Download File"):
    with open(file_path, 'rb') as f:
        file_data = f.read()
    b64_data = base64.b64encode(file_data).decode()
    filename = os.path.basename(file_path)
    href = f'<a href="data:file/markdown;base64,{b64_data}" download="{filename}">{link_text}</a>'
    return href

# Main sidebar
st.sidebar.header("Projects")

# Get all project directories
projects = get_project_directories()

if not projects:
    st.warning("No tutorial projects found in the output directory.")
else:
    # Select project
    selected_project = st.sidebar.selectbox(
        "Select Project",
        projects
    )
    
    # Get all markdown files in the selected project
    md_files = get_markdown_files(selected_project)
    
    if not md_files:
        st.info(f"No markdown files found in project: {selected_project}")
    else:
        # Create sidebar for file selection
        st.sidebar.subheader("Tutorial Files")
        file_options = [name for name, _ in md_files]
        selected_file_name = st.sidebar.radio("Select File", file_options)
        
        # Find the selected file path
        selected_file_path = next(path for name, path in md_files if name == selected_file_name)
        
        # Get file content
        md_content = read_markdown_file(selected_file_path)
        
        # Add a download button for the file
        st.sidebar.markdown("### Actions")
        st.sidebar.markdown(get_download_link(selected_file_path, "📥 Download this file"), unsafe_allow_html=True)
        
        # Display content
        st.markdown(f"## {selected_file_name}")
        
        # Add tabs for viewing content in different formats
        tab1, tab2 = st.tabs(["Rendered", "Raw Markdown"])
        
        with tab1:
            # Handle mermaid diagrams
            if "```mermaid" in md_content:
                # The hacky way to render mermaid in Streamlit
                # Replace mermaid code blocks with HTML
                markdown_blocks = re.split(r'```mermaid\s*\n|```\n', md_content)
                
                for i, block in enumerate(markdown_blocks):
                    if i % 2 == 0:  # Regular markdown content
                        st.markdown(block)
                    else:  # Mermaid diagram
                        st.components.v1.html(
                            f"""
                            <div class="mermaid">
                            {block}
                            </div>
                            <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                            <script>
                            mermaid.initialize({{ startOnLoad: true }});
                            </script>
                            """,
                            height=300
                        )
            else:
                # Regular markdown without diagrams
                st.markdown(md_content)
        
        with tab2:
            # Display raw markdown
            st.text_area("Markdown Source", md_content, height=600)

# Additional info
st.sidebar.markdown("---")
st.sidebar.markdown(
    "Tutorial projects are generated in the 'output' directory. "
    "Use the main app to generate new tutorials."
)

# Back to home button
if st.sidebar.button("🏠 Back to Home"):
    st.switch_page("Home.py") 