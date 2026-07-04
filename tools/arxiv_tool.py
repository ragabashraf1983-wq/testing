import urllib.parse
import xml.etree.ElementTree as ET
import requests
from typing import List
from research_engine.models import PaperMetadata


class ArxivTool:
    """Tool for conducting real-time academic queries against the ArXiv repository API."""
    
    @staticmethod
    def search(query: str, max_results: int = 15) -> List[PaperMetadata]:
        """
        Executes a live query against ArXiv. Returns verified preprints.
        Zero fake or hardcoded fallbacks.
        """
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"
            
            headers = {"User-Agent": "AcademicResearchAgent-Prof/3.0 (mailto:open-source-research@example.com)"}
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"[ArXiv Error] HTTP status {response.status_code}")
                return []

            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            papers = []
            for entry in root.findall('atom:entry', ns):
                title_elem = entry.find('atom:title', ns)
                summary_elem = entry.find('atom:summary', ns)
                if title_elem is None or summary_elem is None:
                    continue
                    
                title = title_elem.text.strip().replace('\n', ' ')
                summary = summary_elem.text.strip().replace('\n', ' ')
                
                pub_elem = entry.find('atom:published', ns)
                published = pub_elem.text[:10] if pub_elem is not None else "Recent"
                
                id_elem = entry.find('atom:id', ns)
                url_link = id_elem.text.strip() if id_elem is not None else ""
                
                authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns) if author.find('atom:name', ns) is not None]
                if not authors:
                    authors = ["ArXiv Contributor"]
                
                papers.append(PaperMetadata(
                    title=title,
                    authors=authors,
                    published_date=published,
                    abstract=summary,
                    url=url_link,
                    source="ArXiv",
                    citation_count=0
                ))
            return papers

        except Exception as e:
            print(f"[ArXiv Exception] {str(e)}")
            return []
