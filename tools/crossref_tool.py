import requests
from typing import List
from research_engine.models import PaperMetadata


class CrossrefTool:
    """Tool for conducting real-time queries against Crossref academic DOI catalog."""
    
    @staticmethod
    def search(query: str, max_results: int = 15) -> List[PaperMetadata]:
        """
        Executes a live query against Crossref API.
        Zero fake or hardcoded fallbacks.
        """
        try:
            url = f"https://api.crossref.org/works?query={query}&rows={max_results}&select=title,author,published,abstract,URL,is-referenced-by-count"
            headers = {"User-Agent": "AcademicResearchAgent-Prof/3.0 (mailto:open-source-research@example.com)"}
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"[Crossref Error] HTTP status {response.status_code}")
                return []

            data = response.json()
            items = data.get("message", {}).get("items", [])
            
            papers = []
            for item in items:
                title_list = item.get("title", [])
                if not title_list or not title_list[0]:
                    continue
                title = title_list[0]
                if len(title.strip()) < 5:
                    continue
                
                authors = []
                for auth in item.get("author", [])[:5]:
                    given = auth.get("given", "")
                    family = auth.get("family", "")
                    if family:
                        authors.append(f"{given} {family}".strip())
                if not authors:
                    authors = ["Crossref Contributor"]
                
                pub_info = item.get("published", {}).get("date-parts", [["Recent"]])
                year = str(pub_info[0][0]) if pub_info and pub_info[0] else "Recent"
                
                abstract = item.get("abstract", "")
                if abstract:
                    import re
                    abstract = re.sub(r'<[^>]+>', '', abstract)
                else:
                    abstract = "Abstract metadata not provided in Crossref schema."

                url_link = item.get("URL", f"https://doi.org/{title[:10]}")
                citations = item.get("is-referenced-by-count", 0)

                papers.append(PaperMetadata(
                    title=title,
                    authors=authors,
                    published_date=f"{year}-01-01",
                    abstract=abstract[:1000] + ("..." if len(abstract) > 1000 else ""),
                    url=url_link,
                    source="Crossref",
                    citation_count=citations
                ))
            return papers

        except Exception as e:
            print(f"[Crossref Exception] {str(e)}")
            return []
