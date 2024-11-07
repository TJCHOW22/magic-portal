import streamlit as st
import datetime
from utils.content_analyzer import analyze_content, extract_text_from_image
from utils.data_manager import save_content, load_content, get_categories
from utils.search_utils import semantic_search
import io
from PIL import Image

st.set_page_config(page_title="Content Management Portal", layout="wide")

def main():
    st.title("Content Management Portal")
    
    # Initialize session state
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'upload'
    
    # Sidebar navigation
    nav_selection = st.sidebar.radio("Navigation", ["Upload Content", "View Content"])
    
    if nav_selection == "Upload Content":
        display_upload_form()
    else:
        display_content_view()

def display_upload_form():
    st.header("Upload Content")
    
    # Add prominent button to switch to content view
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div style='text-align: center; margin: 30px 0; padding: 20px; 
                 background-color: #f0f2f6; border-radius: 10px; 
                 border: 2px solid #4CAF50;'>
                <h2 style='color: #2E7D32;'>📚 Content Library</h2>
                <p style='color: #1B5E20;'>Browse and manage your organized content</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("🔍 Browse Content Library", 
                    use_container_width=True,
                    type="primary",
                    key="browse_library"):
            st.session_state.current_view = 'view'
            st.experimental_rerun()
    
    st.markdown("---")
    
    # Title input
    title = st.text_input("Title", key="title_input")
    
    # Content input options
    content_type = st.radio("Content Type", ["Text", "Link", "Image"])
    
    content = None
    if content_type == "Text":
        content = st.text_area("Enter your text content")
    elif content_type == "Link":
        content = st.text_input("Enter URL")
    else:  # Image
        uploaded_file = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg'])
        if uploaded_file is not None:
            content = uploaded_file.read()
            st.image(content, caption="Uploaded Image", use_column_width=True)
    
    if st.button("Submit", type="primary") and title and content:
        with st.spinner("Processing content..."):
            # Prepare content for analysis
            if content_type == "Image":
                text_content = extract_text_from_image(content)
            else:
                text_content = content
                
            # Analyze content using OpenAI
            analysis = analyze_content(text_content)
            
            # Save content with metadata
            content_data = {
                "title": title,
                "type": content_type,
                "content": content if isinstance(content, str) else None,
                "category": analysis["category"],
                "description": analysis["description"],
                "date": datetime.datetime.now().strftime("%m/%y")
            }
            
            save_content(content_data)
            st.success("Content successfully uploaded and categorized!")

def display_content_view():
    st.header("Content Library")
    
    # Enhanced search interface
    st.markdown("""
        <div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
            <h4 style='color: #1E88E5; margin: 0;'>🔍 Advanced Search</h4>
            <p style='margin: 5px 0;'>Try natural language queries like:</p>
            <ul>
                <li>Show me content about marketing strategies</li>
                <li>Find documents related to sales performance</li>
                <li>Technical documentation about our products</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    # Search and filter options
    col1, col2 = st.columns([2, 1])
    with col1:
        search_query = st.text_input("🔍 Search using natural language")
    with col2:
        categories = get_categories()
        selected_category = st.selectbox("📁 Filter by Category", ["All"] + categories)
    
    # Load content
    content_items = load_content()
    
    # Apply category filter first
    if selected_category != "All":
        content_items = [item for item in content_items 
                        if item["category"] == selected_category]
    
    # Apply semantic search if query exists
    if search_query:
        with st.spinner("Performing semantic search..."):
            content_items = semantic_search(search_query, content_items)
    
    # Group content by category
    content_by_category = {}
    for item in content_items:
        category = item["category"]
        if category not in content_by_category:
            content_by_category[category] = []
        content_by_category[category].append(item)
    
    # Display content organized by category with visual improvements
    if not content_items:
        st.info("No content found matching your criteria.")
    else:
        for category, items in content_by_category.items():
            # Category header with custom styling
            st.markdown(f"""
                <div style='background-color: #f0f2f6; padding: 10px; 
                     border-radius: 5px; margin-top: 20px;'>
                    <h3 style='color: #1E88E5; margin: 0;'>
                        📑 {category}
                    </h3>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            for item in items:
                with st.expander(f"📌 {item['title']} - {item['date']}"):
                    st.markdown(f"""
                        <div style='background-color: #E3F2FD; padding: 10px; 
                             border-radius: 5px; margin-bottom: 10px;'>
                            <p><strong>Category:</strong> {item['category']}</p>
                            <p><strong>Description:</strong> {item['description']}</p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    
                    if item["type"] == "Image":
                        st.image(item["content"], use_column_width=True)
                    elif item["type"] == "Link":
                        st.markdown(f"🔗 [Open Link]({item['content']})")
                    else:
                        st.text_area("Content", item['content'], height=100, disabled=True)
            st.markdown("---")

if __name__ == "__main__":
    main()
