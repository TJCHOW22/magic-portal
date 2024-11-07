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
        # Convert app/link URL to scene URL format
        scene_id = url.split('/')[-1]
        if 'link.excalidraw.com' in url:
            scene_id = url.split('/')[-1]
        elif 'app.excalidraw.com' in url:
            scene_id = url.split('/')[-2]  # Handle app URL format
            
        # Try to fetch the scene data
        api_url = f"https://excalidraw.com/api/v2/scenes/{scene_id}"
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }
        
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise exception for bad status codes
        
        scene_data = response.json()
        
        # Extract text from elements
        texts = []
        if 'elements' in scene_data:
            for element in scene_data['elements']:
                if element.get('type') == 'text' and element.get('text'):
                    texts.append(element['text'])
        
        # If no text found through API, try scraping the webpage
        if not texts:
            page_response = requests.get(url)
            soup = BeautifulSoup(page_response.text, 'html.parser')
            text_elements = soup.find_all(['text', 'tspan', 'div'])
            texts = [elem.get_text().strip() for elem in text_elements if elem.get_text().strip()]
        
        # Combine all found text
        content = ' '.join(texts)
        return content if content else "No text content found in diagram"
            
    except Exception as e:
        print(f"Error extracting Excalidraw content: {str(e)}")
        try:
            # Fallback to basic webpage scraping
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            content = ' '.join(line for line in lines if line)
            return content if content else "Unable to extract text from Excalidraw diagram"
        except:
            return "Unable to extract content from Excalidraw diagram"

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
    """
    Analyze content using OpenAI API to determine category and generate description
    """
    try:
        # If content is a URL, scrape its content
        if content_type == "Link":
            content_to_analyze = scrape_web_content(content)
        else:
            content_to_analyze = content

        prompt = f"""
        Analyze the following content and categorize it into one of these two categories:
        - "Build" (for development, coding, and technical content)
        - "Sales" (for customer acquisition and business-related content)
        
        Also provide a 2-3 sentence description summarizing the content.
        
        Content: {content_to_analyze}
        
        Return the response in the following format:
        {{"category": "selected_category", "description": "generated_description"}}
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.choices[0].message.content
        try:
            result = json.loads(content)
            # Ensure category is either Build or Sales
            if result['category'] not in ['Build', 'Sales']:
                result['category'] = 'Build' if 'technical' in content.lower() or 'coding' in content.lower() else 'Sales'
            return result
        except:
            # Default categorization based on content
            category = 'Build' if 'technical' in content.lower() or 'coding' in content.lower() else 'Sales'
            return {
                "category": category,
                "description": content if len(content) < 200 else content[:197] + "..."
            }
    except Exception as e:
        print(f"Error in content analysis: {str(e)}")
        return {
            "category": "Sales",  # Default to Sales if error occurs
            "description": "Unable to generate description due to an error."
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
