import os
from openai import OpenAI
import json
from PIL import Image
import io

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def analyze_content(content: str) -> dict:
    """
    Analyze content using OpenAI API to determine category and generate description
    """
    prompt = f"""
    Analyze the following content and categorize it into one of these two categories:
    - "Build" (for development, coding, and technical content)
    - "Sales" (for customer acquisition and business-related content)
    
    Also provide a 2-3 sentence description summarizing the content.
    
    Content: {content}
    
    Return the response in the following format:
    {{"category": "selected_category", "description": "generated_description"}}
    """
    
    try:
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
