import numpy as np
from openai import OpenAI
from typing import List, Dict

client = OpenAI()

def get_embedding(text: str) -> List[float]:
    """Get embedding vector for text using OpenAI's API"""
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

def calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def semantic_search(query: str, content_items: List[Dict], threshold: float = 0.7) -> List[Dict]:
    """
    Search content items using semantic similarity
    Returns items sorted by relevance that meet the similarity threshold
    """
    if not query.strip():
        return content_items
        
    try:
        query_embedding = get_embedding(query)
        
        results = []
        for item in content_items:
            # Create a combined text from title and description for matching
            item_text = f"{item['title']} {item['description']}"
            item_embedding = get_embedding(item_text)
            
            similarity = calculate_similarity(query_embedding, item_embedding)
            
            if similarity >= threshold:
                results.append({
                    "item": item,
                    "similarity": similarity
                })
        
        # Sort by similarity score in descending order
        sorted_results = sorted(results, key=lambda x: x["similarity"], reverse=True)
        return [result["item"] for result in sorted_results]
        
    except Exception as e:
        print(f"Error in semantic search: {str(e)}")
        # Fallback to basic text search if semantic search fails
        return [item for item in content_items 
                if query.lower() in item["title"].lower() 
                or query.lower() in item["description"].lower()]
