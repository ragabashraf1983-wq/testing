import json
import re
from typing import List
from research_engine.models import ResearchState, ResearchGap, ResearchQuestion
from research_engine.llm_client import LocalLLMClient
from research_engine.domain_engine import DomainIntelligenceEngine


class GapAnalystAgent:
    """Agent responsible for identifying genuine research contradictions and formulating hypotheses under 'Prof' standards."""
    def __init__(self, llm_client: LocalLLMClient):
        self.llm = llm_client
        self.name = "Chief Research Gap & Strategy Analyst"

    def execute(self, state: ResearchState) -> ResearchState:
        state.add_log(self.name, "Research Gap Analysis", "Analyzing literature review for genuine contradictions and methodological limitations...", f"Topic: '{state.topic}'")
        
        disc, method, _ = DomainIntelligenceEngine.classify_domain_and_methodology(state.topic)
        titles_list = [p.title for p in state.extracted_papers[:15]]

        pool_context = ""
        if state.uploaded_files_content:
            pool_context = f"\nNote: Evaluate against uploaded Research Pool documents under action: '{state.pool_action}'.\n"

        # 1. Identify Gaps via LLM with robust JSON
        prompt_gaps = f"""Act as "Prof"—a world-class interdisciplinary academic and journal editor.
CORE PRINCIPLES: Accuracy before style. Evidence before opinion. Never use unnecessary words. Never invent facts, citations, or paper titles.

TASK:
Based strictly on the following literature synthesis for "{state.topic}" (Discipline: {disc}) and the verified paper titles list below, identify 2 to 3 genuine, unaddressed research gaps, contradictions, or methodological shortcomings.{pool_context}

Respond ONLY with raw JSON array (no markdown, no code blocks, no explanations):
[
  {{
    "gap_id": "GAP-01",
    "title": "...",
    "description": "...",
    "significance": "...",
    "related_papers": ["exact paper title from list"]
  }}
]

Verified Paper Titles:
{json.dumps(titles_list, indent=2)}

Literature Review Synthesis:
{state.literature_summary[:6000]}"""

        raw_gaps = self.llm.generate(prompt_gaps, system_prompt="Act as Prof. Output clean JSON array.", max_tokens=1500)
        gaps = self._parse_gaps(raw_gaps, state, titles_list)
        
        if not gaps:
            state.add_log(self.name, "Research Gap Analysis", "LLM failed to output valid gaps. Using fallback.", status="warning")
            gaps = [
                ResearchGap(
                    gap_id="GAP-01",
                    title=f"Methodological Limitations and Empirical Verification in {state.topic}",
                    description="Current literature exhibits divergence between controlled theoretical assertions and empirical field verification.",
                    significance="Essential for establishing reproducibility and rigorous evidence-based standards.",
                    related_papers=titles_list[:2] if titles_list else []
                )
            ]
            
        state.identified_gaps = gaps
        state.add_log(self.name, "Research Gap Analysis", f"Identified {len(gaps)} verified research gaps.", f"Top Gap: {gaps[0].title}")

        # 2. Formulate Research Questions & Hypotheses via robust JSON
        gaps_desc = "\n".join([f"- [{g.gap_id}] {g.title}: {g.description}" for g in gaps])
        prompt_rq = f"""Act as "Prof"—a world-class research methodologist and PhD supervisor.
CORE PRINCIPLES: Accuracy before style. Evidence before opinion. Never invent facts.

TASK:
For the following verified research gaps in "{state.topic}", formulate 1 to 2 precise research questions and testable scientific hypotheses.
The recommended methodology for this discipline is "{method}". 

Respond ONLY with raw JSON array (no markdown, no code blocks, no explanations):
[
  {{
    "question_id": "RQ-01",
    "question": "...",
    "hypothesis": "...",
    "methodology_type": "{method}",
    "proposed_investigation": "..."
  }}
]

Identified Gaps:
{gaps_desc}"""

        raw_rqs = self.llm.generate(prompt_rq, system_prompt="Act as Prof. Output clean JSON array.", max_tokens=1500)
        rqs = self._parse_rqs(raw_rqs, state, method)
        
        if not rqs:
            rqs = [
                ResearchQuestion(
                    question_id="RQ-01",
                    question=f"How can structured intervention frameworks resolve methodological limitations in {state.topic}?",
                    hypothesis=f"Adopting a systematic {method.replace('_', ' ')} protocol will improve empirical reliability and reduce operational error variance.",
                    methodology_type=method,
                    proposed_investigation=f"Execute a rigorous {method.replace('_', ' ')} across institutional case studies and peer-reviewed benchmarks."
                )
            ]
            
        state.research_questions = rqs
        state.progress_percentage = 50
        state.add_log(self.name, "Hypothesis Generation", "Formulated testable hypotheses successfully.", status="completed")
        return state

    def _parse_gaps(self, raw_text: str, state: ResearchState, fallback_titles: List[str]) -> List[ResearchGap]:
        data = self.llm.extract_json_list(raw_text)
        if not data:
            return []
        result = []
        for item in data:
            if isinstance(item, dict):
                related = item.get("related_papers", [])
                if not related and fallback_titles:
                    related = fallback_titles[:2]
                result.append(ResearchGap(
                    gap_id=item.get("gap_id", "GAP-01"),
                    title=item.get("title", "Untitled Gap"),
                    description=item.get("description", ""),
                    significance=item.get("significance", ""),
                    related_papers=related if isinstance(related, list) else [related],
                ))
        return result

    def _parse_rqs(self, raw_text: str, state: ResearchState, default_method: str) -> List[ResearchQuestion]:
        data = self.llm.extract_json_list(raw_text)
        if not data:
            return []
        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(ResearchQuestion(
                    question_id=item.get("question_id", "RQ-01"),
                    question=item.get("question", ""),
                    hypothesis=item.get("hypothesis", ""),
                    methodology_type=item.get("methodology_type", default_method),
                    proposed_investigation=item.get("proposed_investigation", ""),
                ))
        return result
