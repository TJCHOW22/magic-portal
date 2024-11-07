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
        
        # First try using the Excalidraw API
        api_url = f"https://excalidraw.com/api/v2/scenes/{scene_id}"
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }
        
        response = requests.get(api_url)
        if response.status_code == 200:
            scene_data = response.json()
            texts = []
            
            # Extract text from elements
            if 'elements' in scene_data:
                for element in scene_data['elements']:
                    if element.get('type') == 'text' and element.get('text'):
                        texts.append(element['text'])
            
            if texts:
                return ' '.join(texts)
        
        # If API fails, try direct page scraping
        page_response = requests.get(url)
        soup = BeautifulSoup(page_response.text, 'html.parser')
        
        # Look for text elements in the page
        text_elements = soup.find_all(['text', 'tspan', 'div', 'p'])
        texts = [elem.get_text().strip() for elem in text_elements if elem.get_text().strip()]
        
        # Filter out common UI elements and errors
        filtered_texts = [
            text for text in texts 
            if 'JavaScript' not in text 
            and 'enable' not in text.lower()
            and len(text) > 5
        ]
        
        content = ' '.join(filtered_texts)
        return content if content else "No text content found in diagram"
        
    except Exception as e:
        print(f"Error extracting Excalidraw content: {str(e)}")
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
            if "Unable to extract content" in content_to_analyze:
                return {
                    "category": "Build",
                    "description": "Unable to extract content from the diagram. Please ensure the diagram is publicly accessible."
                }
        else:
            content_to_analyze = content

        # Create a more specific prompt for better analysis
        prompt = f"""
        Analyze the following content and provide:
        1. Category: Either "Build" (for technical/development content) or "Sales" (for business/customer content)
        2. A concise 2-3 sentence description summarizing the key points.
        
        Content to analyze: {content_to_analyze}
        
        Respond in JSON format:
        {{"category": "Build_or_Sales", "description": "Your_summary"}}
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = json.loads(response.choices[0].message.content)
        return {
            "category": result["category"],
            "description": result["description"]
        }
    except Exception as e:
        print(f"Error in content analysis: {str(e)}")
        return {
            "category": "Build",
            "description": f"Error analyzing content: {str(e)}"
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
