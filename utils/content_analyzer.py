import os
from openai import OpenAI
import pytesseract
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
    - "Building" (for development, coding, and technical content)
    - "Sales" (for customer acquisition and business-related content)
    
    Also provide a 2-3 sentence description summarizing the content.
    
    Content: {content}
    
    Return the response in the following format:
    {{"category": "selected_category", "description": "generated_description"}}
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return eval(response.choices[0].message.content)
    except Exception as e:
        print(f"Error in content analysis: {str(e)}")
        return {
            "category": "Uncategorized",
            "description": "Unable to generate description due to an error."
        }

def extract_text_from_image(image_data: bytes) -> str:
    """
    Extract text from image using OCR
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        text = pytesseract.image_to_string(image)
        return text.strip()
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
        - "Building" (for development, coding, and technical content)
        - "Sales" (for customer acquisition and business-related content)
        
        Content: {content}
        
        Return only the category name as a string.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "text"}
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in content recategorization: {str(e)}")
        return "Uncategorized"
