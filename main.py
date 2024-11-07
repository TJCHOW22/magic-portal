import streamlit as st
import datetime
from utils.content_analyzer import analyze_content, extract_text_from_image
from utils.data_manager import save_content, load_content, get_categories
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
    
    if st.button("Submit") and title and content:
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
    
    # Search and filter options
    col1, col2 = st.columns([2, 1])
    with col1:
        search_query = st.text_input("Search by keywords")
    with col2:
        categories = get_categories()
        selected_category = st.selectbox("Filter by Category", ["All"] + categories)
    
    # Load and display content
    content_items = load_content()
    
    # Filter content based on search and category
    if search_query:
        content_items = [item for item in content_items 
                        if search_query.lower() in item["title"].lower() 
                        or search_query.lower() in item["description"].lower()]
    
    if selected_category != "All":
        content_items = [item for item in content_items 
                        if item["category"] == selected_category]
    
    # Display content
    for item in content_items:
        with st.expander(f"{item['title']} - {item['date']}"):
            st.write(f"**Category:** {item['category']}")
            st.write(f"**Description:** {item['description']}")
            if item["type"] == "Image":
                st.image(item["content"])
            else:
                st.write(f"**Content:** {item['content']}")

if __name__ == "__main__":
    main()
