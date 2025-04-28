import streamlit as st
import os

# Set page config
st.set_page_config(
    page_title="AI Codebase Knowledge Builder",
    page_icon="🧠",
    layout="wide"
)

# Main title
st.title("🧠 AI Codebase Knowledge Builder")

# Introduction
st.markdown("""
## Turn any codebase into a beginner-friendly tutorial!

This tool uses AI to analyze your codebase and generate a comprehensive tutorial explaining the core concepts and how they work together.

### What can this tool do?

- 🔍 **Analyze** repositories from GitHub or local directories
- 🧩 **Identify** key abstractions and their relationships
- 📊 **Visualize** the architecture with diagrams
- 📝 **Generate** markdown chapters for each concept
- 📚 **Organize** everything into a complete tutorial
""")

# Display example
st.image("https://github.com/The-Pocket/Tutorial-Codebase-Knowledge/raw/main/assets/example.png", 
         caption="Example of generated tutorial visualization")

# Call to action
st.markdown("---")

# Two-column layout
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Generate a New Tutorial")
    st.markdown("Create a new tutorial from a GitHub repository or local codebase.")
    generate_button = st.button("🚀 Generate Tutorial", use_container_width=True)
    
    if generate_button:
        # Redirect to the generator page
        st.switch_page("pages/01_generate_tutorial.py")

with col2:
    st.markdown("### View Existing Tutorials")
    st.markdown("Browse and view tutorials you've already generated.")
    
    # Count existing tutorials
    tutorial_count = 0
    if os.path.exists("output"):
        tutorial_count = len([d for d in os.listdir("output") if os.path.isdir(os.path.join("output", d))])
    
    if tutorial_count > 0:
        st.success(f"You have {tutorial_count} existing tutorial{'s' if tutorial_count > 1 else ''}!")
    else:
        st.info("No tutorials found. Generate one first!")
    
    view_button = st.button("📚 View Tutorials", use_container_width=True)
    
    if view_button:
        # Redirect to the viewer page
        st.switch_page("pages/02_view_tutorials.py")

# Additional info
st.markdown("---")
st.markdown("""
### How it works:

1. The tool crawls your codebase, extracting key files
2. Advanced LLMs analyze the structure and identify core abstractions 
3. Relationships between components are mapped
4. A logical learning sequence is determined
5. Detailed chapters are generated with examples and diagrams
6. Everything is assembled into a comprehensive tutorial
""")

# Footer
st.markdown("---")
st.markdown(
    "Made with ❤️ using [PocketFlow](https://github.com/The-Pocket/PocketFlow) | "
    "[GitHub Repository](https://github.com/danghung1202/Tutorial-Codebase-Knowledge)"
) 