import streamlit as st
import datetime
import os
from utils.content_analyzer import analyze_content, extract_text_from_image, recategorize_content
from utils.data_manager import save_content, load_content, get_categories, update_uncategorized_content
import io
from PIL import Image
import json
from openai import OpenAI

st.set_page_config(page_title="Content Management Portal", layout="wide")

# Update uncategorized content at startup
try:
    update_uncategorized_content()
except Exception as e:
    st.error(f"Error updating content: {str(e)}")

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
            st.rerun()
    
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
            st.image(content, use_container_width=True)
    
    if st.button("Submit", type="primary") and title and content:
        with st.spinner("Processing content..."):
            try:
                # Prepare content for analysis
                if content_type == "Image":
                    text_content = extract_text_from_image(content)
                else:
                    text_content = content
                    
                # Analyze content using OpenAI
                analysis = analyze_content(text_content, content_type)
                
                # Save content with metadata
                content_data = {
                    "title": title,
                    "type": content_type,
                    "content": content if isinstance(content, str) else None,
                    "category": analysis["category"],
                    "description": analysis["description"],
                    "date": datetime.datetime.now().strftime("%m/%d")
                }
                
                save_content(content_data)
                st.success("Content successfully uploaded and categorized!")
            except Exception as e:
                st.error(f"Error processing content: {str(e)}")

def process_natural_language_query(query: str, content_items: list) -> list:
    """
    Process natural language search query using OpenAI to match content
    """
    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Create embeddings for the query
        query_response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=query
        )
        query_embedding = query_response.data[0].embedding
        
        # Process each content item and calculate similarity
        results = []
        for item in content_items:
            # Create embedding for content description
            content_text = f"{item['title']} {item['description']}"
            content_response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=content_text
            )
            content_embedding = content_response.data[0].embedding
            
            # Calculate cosine similarity
            similarity = sum(a * b for a, b in zip(query_embedding, content_embedding))
            results.append((item, similarity))
        
        # Sort by similarity score
        results.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in results]
    
    except Exception as e:
        st.error(f"Error in natural language search: {str(e)}")
        return content_items

def display_content_view():
    # Add welcome section
    st.markdown('''
        <div style='background: linear-gradient(90deg, #1a237e 0%, #283593 100%);
             color: white; 
             padding: 20px; 
             border-radius: 10px; 
             margin-bottom: 20px;'>
            <h1 style='margin: 0;'>📚 Content Library</h1>
            <p style='margin: 10px 0 0 0;'>Organize and discover your content</p>
        </div>
    ''', unsafe_allow_html=True)
    
    # Load content for stats
    try:
        content_items = load_content()
        # Sort content items by date (most recent first)
        content_items.sort(key=lambda x: x['date'], reverse=True)
    except Exception as e:
        st.error(f"Error loading content: {str(e)}")
        content_items = []
    
    # Add quick stats
    total_items = len(content_items)
    build_items = len([i for i in content_items if i['category'] == 'Build'])
    sales_items = len([i for i in content_items if i['category'] == 'Sales'])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('Total Items', total_items)
    with col2:
        st.metric('Build Items', build_items)
    with col3:
        st.metric('Sales Items', sales_items)
    
    # Update search and filter section
    st.markdown('''
        <div style='background-color: #f8f9fa; 
             padding: 15px; 
             border-radius: 10px; 
             margin: 15px 0;'>
            <h3 style='margin: 0 0 10px 0;'>Search & Filter</h3>
        </div>
    ''', unsafe_allow_html=True)
    
    # Search and filter options
    categories = get_categories()
    col1, col2 = st.columns([2, 1])
    with col1:
        search_query = st.text_input('🔍 Search content...', 
            placeholder='Try "technical documentation" or "sales strategy"')
    with col2:
        selected_category = st.selectbox('📁 Filter by Category', 
            ["All"] + categories,
            format_func=lambda x: f"{x} ({len([i for i in content_items if i['category'] == x]) if x != 'All' else len(content_items)})")
    
    # Apply natural language search if query exists
    if search_query:
        content_items = process_natural_language_query(search_query, content_items)
    
    # Filter by category while maintaining sort order
    if selected_category != "All":
        content_items = [item for item in content_items 
                        if item["category"] == selected_category]
    
    # Group content by category while preserving sort order within each category
    content_by_category = {}
    for item in content_items:
        category = item["category"]
        if category not in content_by_category:
            content_by_category[category] = []
        content_by_category[category].append(item)
    
    # Display content organized by category with side-by-side folders
    if not content_items:
        st.info("No content found matching your criteria.")
    else:
        # Create columns for categories
        cols = st.columns(2)  # Two columns for Build and Sales
        
        # Track which column to use (alternating between 0 and 1)
        col_idx = 0
        
        for category, items in content_by_category.items():
            # Display category in current column
            with cols[col_idx]:
                with st.expander(f"📁 {category} ({len(items)} items)", expanded=True):
                    # Display items in sorted order within each category
                    for item in sorted(items, key=lambda x: x['date'], reverse=True):
                        st.markdown(f'''
                            <div style='background-color: #f8f9fa; 
                                 padding: 15px; 
                                 border-radius: 10px; 
                                 margin: 15px 0;
                                 border-left: 5px solid #1E88E5;
                                 box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                                <div style='display: flex; justify-content: space-between; align-items: center;'>
                                    <h4 style='margin: 0; color: #1a237e;'>📌 {item['title']}</h4>
                                    <span style='color: #666; font-size: 0.9em;'>{item['date']}</span>
                                </div>
                                <div style='margin-top: 10px;'>
                                    <span style='background-color: #e3f2fd; padding: 3px 8px; border-radius: 12px; font-size: 0.9em;'>
                                        {item['category']}
                                    </span>
                                </div>
                                <p style='margin: 10px 0; color: #333;'>{item['description']}</p>
                            </div>
                        ''', unsafe_allow_html=True)
                        
                        if item["type"] == "Image":
                            if item["content"]:
                                try:
                                    st.image(io.BytesIO(item["content"]), use_column_width=True)
                                except:
                                    st.error("Unable to display image")
                        elif item["type"] == "Link":
                            st.markdown(f"🔗 [Open Link]({item['content']})")
                        else:
                            st.text_area("Content", item['content'], height=100, disabled=True)
            
            # Switch to next column
            col_idx = (col_idx + 1) % 2

if __name__ == "__main__":
    main()
