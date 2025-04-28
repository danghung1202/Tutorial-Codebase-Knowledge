import streamlit as st
import os
import tempfile
from pathlib import Path
import dotenv
from flow import create_tutorial_flow
import zipfile

# Load environment variables
dotenv.load_dotenv()

# Default file patterns
DEFAULT_INCLUDE_PATTERNS = {
    "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java", "*.pyi", "*.pyx", 
    "*.c", "*.cc", "*.cpp", "*.h", "*.md", "*.rst", "Dockerfile", 
    "Makefile", "*.yaml", "*.yml",
}

DEFAULT_EXCLUDE_PATTERNS = {
    "*test*", "tests/*", "docs/*", "examples/*", "v1/*", 
    "dist/*", "build/*", "experimental/*", "deprecated/*", 
    "legacy/*", ".git/*", ".github/*", ".next/*", ".vscode/*", "obj/*", "bin/*", "node_modules/*", "*.log"
}

# Set up page config
st.set_page_config(
    page_title="Generate Tutorial",
    page_icon="📝",
    layout="wide"
)

# Title and introduction
st.title("🧠 Generate AI Tutorial")
st.markdown("""
Generate beginner-friendly tutorials from any codebase! This tool will:
1. 🔍 Analyze your codebase
2. 📊 Identify key abstractions and relationships
3. 📝 Create an organized tutorial with chapters
""")

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["📂 Project Source", "⚙️ Configuration", "🤖 LLM Settings"])

# Project Source Tab
with tab1:
    st.header("Project Source")
    source_type = st.radio("Select Source Type:", ("GitHub Repository", "Local Directory"))
    
    repo_url = None
    local_dir = None
    
    if source_type == "GitHub Repository":
        repo_url = st.text_input("GitHub Repository URL", help="e.g., https://github.com/username/repo")
        github_token = st.text_input("GitHub Token (optional)", 
                                    value=os.environ.get('GITHUB_TOKEN', ''),
                                    help="For private repos or to avoid rate limits",
                                    type="password")
    else:
        # Create a session state for storing the extracted directory path
        if 'temp_dir' not in st.session_state:
            st.session_state.temp_dir = None
            
        uploaded_dir = st.file_uploader("Upload Directory (ZIP file)", type=["zip"], 
                                        help="Upload a ZIP file containing your project")
        
        if uploaded_dir:
            try:
                # Create a temporary directory if not already created
                if not st.session_state.temp_dir:
                    temp_dir = tempfile.mkdtemp()
                    st.session_state.temp_dir = temp_dir
                else:
                    temp_dir = st.session_state.temp_dir
                
                # Get project name from zip file name (remove .zip extension)
                zip_name = uploaded_dir.name
                project_name = os.path.splitext(zip_name)[0]
                
                # Create paths
                temp_zip_path = os.path.join(temp_dir, zip_name)
                extract_dir = os.path.join(temp_dir, project_name)
                
                # Ensure the extraction directory exists
                os.makedirs(extract_dir, exist_ok=True)
                
                # Write and extract the zip file
                with open(temp_zip_path, 'wb') as f:
                    f.write(uploaded_dir.getvalue())
                
                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                local_dir = extract_dir
                st.success(f"Successfully extracted files to: {project_name}")
                
            except Exception as e:
                st.error(f"Error extracting ZIP file: {str(e)}")
                local_dir = None
        else:
            st.info("Please upload a ZIP file containing your project")
            local_dir = None

# Configuration Tab
with tab2:
    st.header("Configuration Settings")
    
    # Project name
    project_name = st.text_input("Project Name (optional)", 
                                help="If not provided, will be derived from repo/directory name")
    
    # Output directory
    output_dir = st.text_input("Output Directory", value="output", 
                              help="Base directory for generated tutorial files")
    
    # Language selection
    st.subheader("Language Settings")
    language = st.selectbox(
        "Tutorial Language",
        ["english", "chinese", "spanish", "japanese", "korean", "french", "german"],
        index=0,
        help="Language for the generated tutorial content"
    )
    
    # File patterns
    st.subheader("File Filtering")
    
    # Convert default patterns to comma-separated string for display
    default_include_str = ", ".join(DEFAULT_INCLUDE_PATTERNS)
    default_exclude_str = ", ".join(DEFAULT_EXCLUDE_PATTERNS)
    
    include_patterns_str = st.text_area("Include Patterns", value=default_include_str, 
                                       help="Comma-separated glob patterns to include")
    exclude_patterns_str = st.text_area("Exclude Patterns", value=default_exclude_str, 
                                       help="Comma-separated glob patterns to exclude")
    
    # Convert back to sets
    include_patterns = {pattern.strip() for pattern in include_patterns_str.split(",") if pattern.strip()}
    exclude_patterns = {pattern.strip() for pattern in exclude_patterns_str.split(",") if pattern.strip()}
    
    # Max file size
    max_file_size = st.number_input("Maximum File Size (bytes)", 
                                   value=100000, min_value=1000, max_value=1000000, 
                                   help="Files larger than this will be skipped (100,000 ≈ 100KB)")

# LLM Settings Tab
with tab3:
    st.header("LLM Configuration")
    
    # Model provider selection
    model_provider = st.selectbox(
        "Select LLM Provider", 
        ["gemini", "claude", "openai", "deepseek"]
    )
    
    # Provider-specific settings based on selection
    if model_provider == "gemini":
        st.subheader("Google Gemini Settings")
        model_selection_type = st.radio(
            "Model Selection",
            ["Choose from list", "Custom model"],
            key="gemini_model_type"
        )
        
        if model_selection_type == "Choose from list":
            gemini_model = st.selectbox(
                "Gemini Model", 
                ["gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-flash", "gemini-1.5-pro"]
            )
        else:
            gemini_model = st.text_input(
                "Custom Gemini Model Name",
                placeholder="Enter model name (e.g., gemini-custom-model)"
            )
            
        gemini_api_key = st.text_input(
            "Gemini API Key", 
            value=os.environ.get("GEMINI_API_KEY", ""),
            type="password"
        )
        use_vertex = st.checkbox("Use Vertex AI (Google Cloud)", value=False)
        
        if use_vertex:
            gemini_project_id = st.text_input(
                "Google Cloud Project ID",
                value=os.environ.get("GEMINI_PROJECT_ID", "")
            )
            gemini_location = st.text_input(
                "Google Cloud Location",
                value=os.environ.get("GEMINI_LOCATION", "us-central1")
            )
        
    elif model_provider == "claude":
        st.subheader("Anthropic Claude Settings")
        model_selection_type = st.radio(
            "Model Selection",
            ["Choose from list", "Custom model"],
            key="claude_model_type"
        )
        
        if model_selection_type == "Choose from list":
            claude_model = st.selectbox(
                "Claude Model", 
                ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku"]
            )
        else:
            claude_model = st.text_input(
                "Custom Claude Model Name",
                placeholder="Enter model name (e.g., claude-custom-model)"
            )
            
        claude_api_key = st.text_input(
            "Anthropic API Key", 
            value=os.environ.get("ANTHROPIC_API_KEY", ""),
            type="password"
        )
        
    elif model_provider == "openai":
        st.subheader("OpenAI Settings")
        model_selection_type = st.radio(
            "Model Selection",
            ["Choose from list", "Custom model"],
            key="openai_model_type"
        )
        
        if model_selection_type == "Choose from list":
            openai_model = st.selectbox(
                "OpenAI Model", 
                ["o1", "gpt-4o", "gpt-4", "gpt-3.5-turbo"]
            )
        else:
            openai_model = st.text_input(
                "Custom OpenAI Model Name",
                placeholder="Enter model name (e.g., ft:gpt-4-0125-preview:custom:model)"
            )
            
        openai_api_key = st.text_input(
            "OpenAI API Key", 
            value=os.environ.get("OPENAI_API_KEY", ""),
            type="password"
        )
        
    elif model_provider == "deepseek":
        st.subheader("DeepSeek Settings")
        model_selection_type = st.radio(
            "Model Selection",
            ["Choose from list", "Custom model"],
            key="deepseek_model_type"
        )
        
        if model_selection_type == "Choose from list":
            deepseek_model = st.selectbox(
                "DeepSeek Model", 
                ["deepseek-chat", "deepseek-coder"]
            )
        else:
            deepseek_model = st.text_input(
                "Custom DeepSeek Model Name",
                placeholder="Enter model name (e.g., deepseek-custom-model)"
            )
            
        deepseek_api_key = st.text_input(
            "DeepSeek API Key", 
            value=os.environ.get("DEEPSEEK_API_KEY", ""),
            type="password"
        )
    
    # Common LLM settings
    st.subheader("General LLM Settings")
    use_cache = st.checkbox("Use LLM Response Cache", value=True, 
                          help="Cache responses to avoid repeated API calls")

# Create a collapsible section for advanced settings
with st.expander("Advanced Settings"):
    st.markdown("### Logging Settings")
    log_dir = st.text_input("Log Directory", value="logs", 
                           help="Directory for LLM call logs")

# Run button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_button = st.button("🚀 Generate Tutorial", type="primary", use_container_width=True)

# Show progress and run the flow when button is clicked
if run_button:
    # Validate inputs
    if source_type == "GitHub Repository" and not repo_url:
        st.error("Please provide a GitHub repository URL")
    elif source_type == "Local Directory" and not local_dir:
        st.error("Please upload a ZIP file containing your project")
    else:
        # Set environment variables for LLM
        if model_provider == "gemini":
            os.environ["GEMINI_MODEL"] = gemini_model
            os.environ["GEMINI_API_KEY"] = gemini_api_key
            if use_vertex:
                os.environ["GEMINI_PROJECT_ID"] = gemini_project_id
                os.environ["GEMINI_LOCATION"] = gemini_location
        elif model_provider == "claude":
            os.environ["ANTHROPIC_API_KEY"] = claude_api_key
        elif model_provider == "openai":
            os.environ["OPENAI_API_KEY"] = openai_api_key
        elif model_provider == "deepseek":
            os.environ["DEEPSEEK_API_KEY"] = deepseek_api_key
        
        # Set logging directory
        os.environ["LOG_DIR"] = log_dir
        
        # Initialize the shared dictionary with inputs
        shared = {
            "repo_url": repo_url,
            "local_dir": local_dir,
            "project_name": project_name if project_name else None,  # Can be None, FetchRepo will derive it
            "github_token": github_token if source_type == "GitHub Repository" else None,
            "output_dir": output_dir,
            
            # Add include/exclude patterns and max file size
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns,
            "max_file_size": max_file_size,

            # Add language for multi-language support
            "language": language,
            
            # Add LLM settings to shared for nodes to access
            "llm_settings": {
                "model_provider": model_provider,
                "specific_model": locals().get(f"{model_provider}_model", None),
                "use_cache": use_cache
            },
            
            # Outputs will be populated by the nodes
            "files": [],
            "abstractions": [],
            "relationships": {},
            "chapter_order": [],
            "chapters": [],
            "final_output_dir": None
        }
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Create the flow instance
        tutorial_flow = create_tutorial_flow()
        
        try:
            # Show stages of the flow
            stages = ["Fetching repository", "Identifying abstractions", 
                     "Analyzing relationships", "Ordering chapters", 
                     "Writing chapters", "Combining tutorial"]
            
            for i, stage in enumerate(stages):
                status_text.text(f"Step {i+1}/{len(stages)}: {stage}...")
                progress_bar.progress((i) / len(stages))
                
                # Add a small delay for visual effect
                import time
                time.sleep(0.5)
            
            # Run the flow
            tutorial_flow.run(shared)
            
            # Update progress to complete
            progress_bar.progress(1.0)
            status_text.text("✅ Tutorial generated successfully!")
            
            # Show success message and link to output
            st.success(f"Tutorial generated successfully in: {shared['final_output_dir']}")
            
            # Provide a link to the View Tutorials page
            st.info("Go to the View Tutorials page to browse your generated tutorial!")
            
            if st.button("📚 View Generated Tutorial"):
                import streamlit as st
                st.switch_page("pages/02_view_tutorials.py")
            
        except Exception as e:
            st.error(f"Error generating tutorial: {str(e)}")
            st.exception(e) 