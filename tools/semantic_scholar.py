import requests
from typing import List
from research_engine.models import PaperMetadata


class SemanticScholarTool:
    """Tool for conducting real-time queries against Semantic Scholar Academic Graph API."""
    
    @staticmethod
    def search(query: str, max_results: int = 15) -> List[PaperMetadata]:
        """
        Executes a live query against Semantic Scholar.
        Zero fake or hardcoded fallbacks.
        """
        try:
            url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit={max_results}&fields=title,authors,year,abstract,citationCount,url"
            headers = {"User-Agent": "AcademicResearchAgent-Prof/3.0 (mailto:open-source-research@example.com)"}
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"[Semantic Scholar Error] HTTP status {response.status_code}")
                return []

            data = response.json()
            results = data.get("data", [])
            
            papers = []
            for item in results:
                title = item.get("title")
                if not title or len(title.strip()) < 5:
                    continue
                
                authors = [auth.get("name", "Unknown Author") for auth in item.get("authors", [])[:5]]
                if not authors:
                    authors = ["Semantic Scholar Contributor"]
                    
                year = str(item.get("year") or "Recent")
                abstract = item.get("abstract") or "Abstract not provided in Semantic Scholar response."
                url_link = item.get("url") or f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}"
                citations = item.get("citationCount", 0)

                papers.append(PaperMetadata(
                    title=title,
                    authors=authors,
                    published_date=f"{year}-01-01",
                    abstract=abstract[:1000] + ("..." if len(abstract) > 1000 else ""),
                    url=url_link,
                    source="Semantic Scholar",
                    citation_count=citations
                ))
            return papers

        except Exception as e:
            print(f"[Semantic Scholar Exception] {str(e)}")
            return []
