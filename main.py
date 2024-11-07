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
        
        # Return only items with similarity above threshold (0.7)
        return [item for item, score in results if score > 0.7]
    
    except Exception as e:
        st.error(f"Error in natural language search: {str(e)}")
        return content_items

def main():
    # Dark theme styling
    st.markdown('''
        <style>
            .stApp {
                background-color: #1a1f3c;  /* Dark navy blue */
                color: #ffffff;  /* White text */
            }
            /* Make all text white by default */
            p, h1, h2, h3, h4, h5, h6 {
                color: #ffffff !important;
            }
            /* Style content cards */
            div[data-testid="stExpander"] {
                background-color: #232b50;  /* Slightly lighter navy blue */
                border-radius: 10px;
                padding: 10px;
                margin: 10px 0;
            }
            /* Style buttons */
            button {
                background-color: #3949ab !important;
                color: white !important;
            }
            /* Style text inputs */
            input[type="text"], textarea {
                background-color: #2a325a !important;
                color: white !important;
                border: 1px solid #3949ab !important;
            }
        </style>
    ''', unsafe_allow_html=True)
    
    # Sidebar navigation
    nav_selection = st.sidebar.radio("Navigation", ["Upload Content", "View Content"])
    
    if nav_selection == "Upload Content":
        display_upload_form()
    else:
        display_content_view()

def display_upload_form():
    st.markdown('''
        <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
            <div style="background: #232b50; padding: 30px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.2);">
                <h1 style="color: #ffffff; margin-bottom: 20px;">📤 Upload Content</h1>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div style="background: #232b50; padding: 30px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); margin: 20px 0;">', unsafe_allow_html=True)
        
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
        
        st.markdown('</div>', unsafe_allow_html=True)
        
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

def display_content_view():
    st.markdown('''
        <div style="background: linear-gradient(90deg, #232b50 0%, #2a325a 100%);
             color: white; 
             padding: 20px; 
             border-radius: 15px; 
             margin-bottom: 20px;
             box-shadow: 0 2px 10px rgba(0,0,0,0.2);">
            <h1 style="margin: 0;">📚 Content Library</h1>
            <p style="margin: 10px 0 0 0;">Organize and discover your content</p>
        </div>
    ''', unsafe_allow_html=True)
    
    # Load content
    try:
        content_items = load_content()
        content_items.sort(key=lambda x: x['date'], reverse=True)
    except Exception as e:
        st.error(f"Error loading content: {str(e)}")
        content_items = []
    
    # Quick stats
    total_items = len(content_items)
    build_items = len([i for i in content_items if i['category'] == 'Build'])
    sales_items = len([i for i in content_items if i['category'] == 'Sales'])
    
    metrics = [
        {"label": "Total Items", "value": total_items},
        {"label": "Build Items", "value": build_items},
        {"label": "Sales Items", "value": sales_items}
    ]
    
    cols = st.columns(3)
    for idx, metric in enumerate(metrics):
        with cols[idx]:
            st.markdown(f'''
                <div style="background: #232b50; padding: 20px; border-radius: 15px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.2);">
                    <h3 style="color: #ffffff; margin: 0;">{metric['value']}</h3>
                    <p style="color: #a0a0a0; margin: 5px 0 0 0;">{metric['label']}</p>
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
        st.info("Searching using natural language processing...")
        content_items = process_natural_language_query(search_query, content_items)
    
    # Filter by category
    if selected_category != "All":
        content_items = [item for item in content_items 
                        if item["category"] == selected_category]
    
    # Group content by category
    content_by_category = {}
    for item in content_items:
        category = item["category"]
        if category not in content_by_category:
            content_by_category[category] = []
        content_by_category[category].append(item)
    
    # Display content
    if not content_items:
        st.info("No content found matching your criteria.")
    else:
        cols = st.columns(2)
        col_idx = 0
        
        for category, items in content_by_category.items():
            with cols[col_idx]:
                with st.expander(f"📁 {category} ({len(items)} items)", expanded=True):
                    for item in sorted(items, key=lambda x: x['date'], reverse=True):
                        # Display content card header
                        st.markdown(f'''
                            <div style="background: #000000; 
                                 padding: 20px; 
                                 border-radius: 15px;
                                 margin: 15px 0;
                                 border-left: 5px solid #3949ab;
                                 box-shadow: 0 2px 10px rgba(0,0,0,0.2);">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <h3 style="margin: 0; color: #ffffff;">{item['title']}</h3>
                                    <span style="color: #a0a0a0; font-size: 0.9em;">{item['date']}</span>
                                </div>
                                <div style="margin: 10px 0;">
                                    <span style="background: #3949ab; 
                                          padding: 5px 10px; 
                                          border-radius: 15px; 
                                          font-size: 0.9em;
                                          color: white;">
                                        {item['category']}
                                    </span>
                                </div>
                                <p style="margin: 15px 0; color: #ffffff; line-height: 1.6;">
                                    {item['description']}
                                </p>
                            </div>
                        ''', unsafe_allow_html=True)

                        # Display content based on type
                        if item["type"] == "Text":
                            with st.expander("View Content"):
                                st.markdown(f'''
                                    <div style="background: #000000; 
                                          padding: 15px;
                                          border-radius: 8px;">
                                        <pre style="color: #ffffff; 
                                              white-space: pre-wrap;
                                              margin: 0;
                                              font-family: monospace;">
                                            {item['content']}
                                        </pre>
                                    </div>
                                ''', unsafe_allow_html=True)
                        elif item["type"] == "Link":
                            st.markdown(f'''
                                <a href="{item['content']}" target="_blank" 
                                   style="display: inline-block; 
                                          background: #3949ab; 
                                          color: white; 
                                          text-decoration: none; 
                                          padding: 8px 15px; 
                                          border-radius: 8px; 
                                          margin-top: 10px;">
                                    🔗 Open Link
                                </a>
                            ''', unsafe_allow_html=True)
                        elif item["type"] == "Image" and item["content"]:
                            try:
                                st.image(io.BytesIO(item["content"]), use_container_width=True)
                            except:
                                st.error("Unable to display image")
            
            col_idx = (col_idx + 1) % 2

if __name__ == "__main__":
    main()
