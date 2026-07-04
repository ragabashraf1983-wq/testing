import requests
from typing import List, Dict


class WebSearchTool:
    """Tool for querying live search engines and Wikipedia for academic terminology."""
    
    @staticmethod
    def search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Executes live search.
        Zero fake or hardcoded fallbacks.
        """
        results = []
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                ddg_res = list(ddgs.text(query, max_results=max_results))
                for r in ddg_res:
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")
                    })
            if results:
                return results
        except Exception:
            pass

        try:
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.split()[0]}"
            resp = requests.get(wiki_url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                results.append({
                    "title": data.get("title", query),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    "snippet": data.get("extract", "")
                })
        except Exception:
            pass

        return results
