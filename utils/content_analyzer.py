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
    Analyze the following content and provide:
    1. A category (choose from: Sales, Marketing, Tech, Finance, Operations)
    2. A 2-3 sentence description summarizing the content
    
    Content: {content}
    
    Return the response in the following format:
    {{"category": "selected_category", "description": "generated_description"}}
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json"}
        )
        
        return eval(response.choices[0].message.content)
    except Exception as e:
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
        return "Unable to extract text from image"
