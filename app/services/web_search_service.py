"""
Web search service using DuckDuckGo API
"""
from duckduckgo_search import DDGS
from typing import List, Dict


class WebSearchService:
    """Service for web search integration"""
    
    def __init__(self):
        self.ddgs = DDGS()
    
    async def search(
        self,
        query: str,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Search the web and return results
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results with title, snippet, url
        """
        try:
            results = []
            
            # DuckDuckGo search (sync operation)
            for result in self.ddgs.text(query, max_results=max_results):
                results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "url": result.get("href", ""),
                    "source": "duckduckgo"
                })
            
            return results
            
        except Exception as e:
            return [{
                "error": str(e),
                "query": query,
                "message": "Web search temporarily unavailable"
            }]
