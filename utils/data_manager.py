import json
import os
from typing import List, Dict

DATA_FILE = "data/content.json"

def ensure_data_file():
    """Ensure the data file exists"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)

def save_content(content_data: Dict) -> None:
    """Save content to JSON file"""
    ensure_data_file()
    
    try:
        with open(DATA_FILE, 'r') as f:
            existing_content = json.load(f)
    except:
        existing_content = []
    
    existing_content.append(content_data)
    
    with open(DATA_FILE, 'w') as f:
        json.dump(existing_content, f)

def load_content() -> List[Dict]:
    """Load all content from JSON file"""
    ensure_data_file()
    
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def get_categories() -> List[str]:
    """Get unique categories from stored content"""
    content = load_content()
    categories = set(item["category"] for item in content)
    return sorted(list(categories))
