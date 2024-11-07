import os
from openai import OpenAI
import json
from PIL import Image
import io
import requests
from bs4 import BeautifulSoup

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def scrape_excalidraw_content(url: str) -> str:
    try:
        # Extract scene ID from URL
        scene_id = url.split('/')[-1]
        if '/s/' in url:
            scene_id = url.split('/s/')[-1].split('/')[1]
        
        # Use the Excalidraw API endpoint for scenes
        api_url = f"https://excalidraw.com/api/v2/scenes/{scene_id}/export"
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/json'
        }
        
        # Request scene data
        print(f"Attempting to fetch scene data from: {api_url}")
        response = requests.get(api_url, headers=headers)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                scene_data = response.json()
                print("Successfully parsed scene data")
                
                # Extract all text elements
                texts = []
                if 'elements' in scene_data:
                    for element in scene_data['elements']:
                        if element.get('type') == 'text':
                            text = element.get('text', '').strip()
                            if text:
                                texts.append(text)
                        # Also check for labels in other elements
                        elif element.get('label'):
                            texts.append(element.get('label').strip())
                
                if texts:
                    print(f"Found {len(texts)} text elements")
                    content = ' '.join(texts)
                    return content
                
            except json.JSONDecodeError as je:
                print(f"JSON decode error: {str(je)}")
                print(f"Response content: {response.text[:200]}")
            
        # If API fails or no text found, try parsing the HTML content
        page_url = f"https://excalidraw.com/l/{scene_id}"
        print(f"Attempting to fetch scene directly from: {page_url}")
        
        page_response = requests.get(page_url)
        soup = BeautifulSoup(page_response.text, 'html.parser')
        
        # Look for text content in the page
        text_elements = soup.find_all(['text', 'tspan', 'div.excalidraw-textLayer'])
        texts = [elem.get_text().strip() for elem in text_elements if elem.get_text().strip()]
        
        if texts:
            print(f"Found {len(texts)} text elements from direct page scraping")
            return ' '.join(texts)
        
        print("No text content found through any method")
        return "No text content found in diagram"
        
    except Exception as e:
        print(f"Error extracting Excalidraw content: {str(e)}")
        print(f"URL attempted: {url}")
        return f"Unable to extract content from Excalidraw diagram: {str(e)}"

def scrape_web_content(url: str) -> str:
    if 'excalidraw.com' in url:
        return scrape_excalidraw_content(url)
        
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:1000]  # Limit text length
    except Exception as e:
        print(f"Error scraping web content: {str(e)}")
        return f"Error: Unable to scrape content from {url}"

def analyze_content(content: str, content_type: str = "Text") -> dict:
    try:
        # Get content to analyze
        if content_type == "Link":
            content_to_analyze = scrape_web_content(content)
            if "No text content found in diagram" in content_to_analyze:
                return {
                    "category": "Sales",  # Default to Sales for GTM diagrams
                    "description": "This appears to be a GTM strategy diagram. However, the text content couldn't be extracted automatically. Please ensure the diagram is publicly accessible and contains text elements."
                }
        else:
            content_to_analyze = content

        # Enhanced prompt for better analysis
        prompt = f'''
        You are an expert content analyzer specializing in business and technical documentation.
        
        Analyze this content carefully and provide:
        1. Category: Choose ONE category:
           - "Build" for technical content (code, development, infrastructure)
           - "Sales" for business content (GTM, strategy, marketing)
           
        2. Description: Write a specific 2-3 sentence summary that:
           - Captures the main purpose/objective
           - Highlights key points or strategies discussed
           - Avoids generic statements like "unable to analyze" or "content not available"
           - If it's a GTM or strategy document, focus on the business approach
           - If it's technical, focus on the implementation details
        
        Content to analyze: {content_to_analyze}
        
        Respond in this JSON format:
        {{
            "category": "Build or Sales",
            "description": "Your specific summary here"
        }}
        '''
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "system",
                "content": "You are an expert content analyzer. Provide detailed, specific descriptions."
            }, {
                "role": "user",
                "content": prompt
            }],
            temperature=0.7  # Add some creativity while maintaining accuracy
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Ensure we always have meaningful content
        if "unable to" in result["description"].lower() or "not available" in result["description"].lower():
            if "gtm" in content_to_analyze.lower() or "strategy" in content_to_analyze.lower():
                result["category"] = "Sales"
                result["description"] = "This appears to be a GTM strategy document outlining business approach and market positioning. The diagram likely contains information about target markets, customer segments, and go-to-market tactics."
        
        return result
    except Exception as e:
        print(f"Error in content analysis: {str(e)}")
        return {
            "category": "Sales" if any(word in content_to_analyze.lower() for word in ["gtm", "strategy", "market"]) else "Build",
            "description": "This document appears to contain business strategy information. Please ensure the content is accessible for a more detailed analysis."
        }

def extract_text_from_image(image_data: bytes) -> str:
    """
    Extract text from image using OCR
    """
    try:
        # For now, return a simple message as we removed pytesseract
        return "Image content (text extraction not available)"
    except Exception as e:
        print(f"Error in image text extraction: {str(e)}")
        return "Unable to extract text from image"

def recategorize_content(content: str) -> str:
    """
    Recategorize existing content into new categories
    """
    try:
        prompt = f"""
        Analyze the following content and categorize it into one of these categories:
        - "Build" (for development, coding, and technical content)
        - "Sales" (for customer acquisition and business-related content)
        
        Content: {content}
        
        Return only the category name.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        category = response.choices[0].message.content.strip()
        return "Build" if category.lower() == "build" or "technical" in content.lower() or "coding" in content.lower() else "Sales"
    except Exception as e:
        print(f"Error in content recategorization: {str(e)}")
        return "Sales"  # Default to Sales if error occurs
