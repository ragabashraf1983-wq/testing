import json
from typing import List
from research_engine.models import ResearchState, PaperMetadata
from research_engine.llm_client import LocalLLMClient
from research_engine.domain_engine import DomainIntelligenceEngine
from tools import ArxivTool, OpenAlexTool, SemanticScholarTool, CrossrefTool


class LiteratureScoutAgent:
    """Agent responsible for multi-database retrieval and analyzing uploaded Research Pool documents."""
    def __init__(self, llm_client: LocalLLMClient):
        self.llm = llm_client
        self.name = "Literature Scout & Bibliometric Analyst"

    def execute(self, state: ResearchState) -> ResearchState:
        state.add_log(self.name, "Literature Retrieval", "Initiating live 4-database search across global academic repositories...", f"Topic: '{state.topic}'")
        
        # 1. Query ArXiv
        state.add_log(self.name, "Literature Retrieval", "Scraping ArXiv preprint repository...", "Fetching up to 15 preprints")
        arxiv_papers = ArxivTool.search(state.topic, max_results=15)
        
        # 2. Query OpenAlex
        state.add_log(self.name, "Literature Retrieval", "Scraping OpenAlex open-access catalog (250M+ works)...", "Fetching up to 20 publications")
        openalex_papers = OpenAlexTool.search(state.topic, max_results=20)

        # 3. Query Semantic Scholar
        state.add_log(self.name, "Literature Retrieval", "Scraping Semantic Scholar Academic Graph API...", "Fetching up to 15 peer-reviewed works")
        semantic_papers = SemanticScholarTool.search(state.topic, max_results=15)

        # 4. Query Crossref
        state.add_log(self.name, "Literature Retrieval", "Scraping Crossref DOI metadata index...", "Fetching up to 15 DOI records")
        crossref_papers = CrossrefTool.search(state.topic, max_results=15)
        
        # Deduplicate by clean title
        raw_papers = arxiv_papers + openalex_papers + semantic_papers + crossref_papers
        seen_titles = set()
        unique_papers = []
        for p in raw_papers:
            clean_t = "".join(e for e in p.title.lower() if e.isalnum())
            if clean_t not in seen_titles and len(clean_t) > 5:
                seen_titles.add(clean_t)
                unique_papers.append(p)

        # Sort by citation count descending
        unique_papers.sort(key=lambda x: x.citation_count or 0, reverse=True)
        state.extracted_papers = unique_papers[:30]
        
        if not state.extracted_papers:
            state.add_log(self.name, "Literature Retrieval", "No verified academic papers could be extracted.", status="error")
            state.literature_summary = "[ERROR] Zero academic publications were retrieved for this query across all 4 databases. Please verify your internet connection or refine your topic."
            return state

        state.add_log(self.name, "Literature Retrieval", f"Extracted & deduplicated {len(state.extracted_papers)} verified papers across 4 databases.", "Executing deep analytical synthesis...")

        disc, method, method_desc = DomainIntelligenceEngine.classify_domain_and_methodology(state.topic)
        state.add_log(self.name, "Literature Retrieval", f"Discipline Classified: {disc}", f"Recommended Methodology: {method.upper()}")

        abstracts_context = "\n\n".join([
            f"Title: {p.title}\nAuthors: {', '.join(p.authors[:3])}\nSource: {p.source} ({p.published_date}) Citations: {p.citation_count}\nAbstract: {p.abstract}"
            for p in state.extracted_papers[:12]
        ])
        
        # Document Pool Context
        pool_context = ""
        if state.uploaded_files_content:
            pool_context = "\n--- RESEARCH POOL UPLOADED DOCUMENTS ---\n" + "\n\n".join([
                f"File: {doc['filename']}\nContent Excerpt: {doc['content'][:1500]}..."
                for doc in state.uploaded_files_content
            ]) + f"\nRequested Pool Action: {state.pool_action}\n----------------------------------------\n"

        prompt = f"""Act as "Prof"—a world-class interdisciplinary academic with the combined expertise of: Full Professor, Journal Editor-in-Chief, Scientific Reviewer, and Research Methodologist.

CORE PRINCIPLES:
1. Accuracy before style. 2. Evidence before opinion. 3. Precision before completeness. 4. Simplicity before complexity. 5. Never use unnecessary words. 6. Never invent facts, citations, results, or references. 7. State uncertainty explicitly when evidence is insufficient. 8. Every sentence must contribute value.

TASK:
Conduct a rigorous, publication-grade literature review synthesis for: "{state.topic}" (Discipline: {disc}).
Target Deliverable Type: "{state.target_deliverable}".

Analyze the REAL scraped abstracts retrieved from global academic databases below.{pool_context}

Write a natural, concise, direct, professional academic synthesis covering:
1. Dominant Methodological Paradigms (Explain how researchers approach this problem without forcing computational simulation if inappropriate).
2. Empirical Findings & Academic Consensus (Cite specific authors and publication years strictly from the scraped list below).
3. Critical Contradictions, Methodological Limitations & Unanswered Gaps.
{f"4. Analysis of User's Uploaded Document Pool: Evaluate the uploaded files under the requested action: '{state.pool_action}'." if pool_context else ""}

Scraped Academic Abstracts:
{abstracts_context}"""

        system_prompt = "Act as Prof. You are a world-class academic bibliometrician and reviewer. Zero fluff, zero invented citations."
        summary = self.llm.generate(prompt=prompt, system_prompt=system_prompt, max_tokens=2200)
        
        state.literature_summary = summary
        state.progress_percentage = 25
        state.add_log(self.name, "Literature Retrieval", "Multi-database literature synthesis completed.", status="completed")
        return state
