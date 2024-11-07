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
            if not content_to_analyze or "Unable to extract content" in content_to_analyze:
                return {
                    "category": "Build",
                    "description": "Unable to extract content from the diagram. Please ensure the diagram is publicly accessible."
                }
        else:
            content_to_analyze = content

        # Create a more specific prompt for better analysis
        prompt = f"""
        Analyze the following content and provide:
        1. Category: Categorize as either:
           - "Build" if the content is about technical development, coding, or infrastructure
           - "Sales" if the content is about business strategy, customer acquisition, or marketing
        2. Description: Write a clear 2-3 sentence summary of the key points in the content.
           Focus on the main ideas and objectives discussed.

        Content to analyze: {content_to_analyze}

        Respond in JSON format like this:
        {{
            "category": "Build or Sales",
            "description": "Your concise summary here"
        }}
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "system",
                "content": "You are an expert content analyzer. Your task is to categorize content and write clear, concise summaries."
            }, {
                "role": "user",
                "content": prompt
            }]
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Validate the category
        if result["category"] not in ["Build", "Sales"]:
            # Default categorization based on keywords
            result["category"] = "Build" if any(word in content_to_analyze.lower() 
                for word in ["technical", "code", "develop", "infrastructure", "api"]) else "Sales"
        
        return {
            "category": result["category"],
            "description": result["description"]
        }
    except Exception as e:
        print(f"Error in content analysis: {str(e)}")
        # Make a simpler attempt at categorization
        is_technical = any(word in content_to_analyze.lower() 
            for word in ["technical", "code", "develop", "infrastructure", "api"])
        return {
            "category": "Build" if is_technical else "Sales",
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
