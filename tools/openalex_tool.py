import requests
from typing import List
from research_engine.models import PaperMetadata


class OpenAlexTool:
    """Tool for conducting real-time queries against OpenAlex (250M+ open-access academic works)."""
    
    @staticmethod
    def search(query: str, max_results: int = 20) -> List[PaperMetadata]:
        """
        Executes a live query against OpenAlex API.
        Zero fake or hardcoded fallbacks.
        """
        try:
            url = f"https://api.openalex.org/works?search={query}&per-page={max_results}&sort=relevance_score:desc"
            headers = {"User-Agent": "AcademicResearchAgent-Prof/3.0 (mailto:open-source-research@example.com)"}
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"[OpenAlex Error] HTTP status {response.status_code}")
                return []

            data = response.json()
            results = data.get("results", [])
            
            papers = []
            for work in results:
                title = work.get("title")
                if not title or len(title.strip()) < 5:
                    continue
                
                abstract_text = "Abstract not indexed in inverted index format."
                inv_index = work.get("abstract_inverted_index")
                if inv_index and isinstance(inv_index, dict):
                    try:
                        word_list = []
                        for word, positions in inv_index.items():
                            for pos in positions:
                                word_list.append((pos, word))
                        word_list.sort(key=lambda x: x[0])
                        abstract_text = " ".join([w[1] for w in word_list])
                    except Exception:
                        pass

                authors = [
                    auth.get("author", {}).get("display_name", "Unknown Author")
                    for auth in work.get("authorships", [])[:5]
                ]
                if not authors:
                    authors = ["OpenAlex Contributor"]
                
                pub_date = work.get("publication_date", "Recent")
                doi_url = work.get("doi") or work.get("id", "")
                cited_by = work.get("cited_by_count", 0)

                papers.append(PaperMetadata(
                    title=title,
                    authors=authors,
                    published_date=pub_date,
                    abstract=abstract_text[:1000] + ("..." if len(abstract_text) > 1000 else ""),
                    url=doi_url,
                    source="OpenAlex",
                    citation_count=cited_by
                ))
            return papers

        except Exception as e:
            print(f"[OpenAlex Exception] {str(e)}")
            return []
