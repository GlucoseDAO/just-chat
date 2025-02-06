from typing import List, Dict
from duckduckgo_search import DDGS
import time

def search_web(query: str, num_results: int = 5) -> List[Dict]:
    """
    Perform a DuckDuckGo web search and return results
    
    Args:
        query: Search query string
        num_results: Number of results to return (default: 5, max recommended: 25)
        
    Returns:
        List of dictionaries containing search results
    """

    print(f"Searching the web for: {query}")
    try:
        # Limit number of results to avoid rate limiting
        num_results = min(num_results, 25)  # Cap at 25 results per request
        
        # Add delay between requests if needed
        time.sleep(0.5)  # 500ms delay to be safe
        
        # Create a DDGS instance and perform the search
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
        
        if not results:
            return []
            
        return [{
            'title': item['title'],
            'link': item['link'],
            'snippet': item['body']
        } for item in results]
        
    except Exception as e:
        print(f"Error performing web search: {e}")
        return [] 