# Keeping the same content, just updating the text content display section at line 301
import streamlit as st
import datetime
import os
from utils.content_analyzer import analyze_content, extract_text_from_image, recategorize_content
from utils.data_manager import save_content, load_content, get_categories, update_uncategorized_content
import io
from PIL import Image
import json
from openai import OpenAI

# Previous code remains the same until line 301
[Previous content remains unchanged until line 301]

                        elif item["type"] == "Text":
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
                                    <details>
                                        <summary style="color: #ffffff; 
                                                  cursor: pointer; 
                                                  padding: 5px;
                                                  user-select: none;
                                                  background: #3949ab;
                                                  display: inline-block;
                                                  border-radius: 8px;
                                                  padding: 8px 15px;">
                                            View Content
                                        </summary>
                                        <div style="color: #ffffff;
                                              padding: 10px;
                                              margin-top: 10px;
                                              white-space: pre-wrap;">
                                            {item['content']}
                                        </div>
                                    </details>
                                </div>
                            ''', unsafe_allow_html=True)
            
            col_idx = (col_idx + 1) % 2

[Rest of the code remains unchanged]
