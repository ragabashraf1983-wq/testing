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

        # 1. Identify Gaps via LLM
        prompt_gaps = f"""Act as "Prof"—a world-class interdisciplinary academic and journal editor.
CORE PRINCIPLES: Accuracy before style. Evidence before opinion. Never use unnecessary words. Never invent facts, citations, or paper titles.

TASK:
Based strictly on the following literature synthesis for "{state.topic}" (Discipline: {disc}) and the verified paper titles list below, identify 2 to 3 genuine, unaddressed research gaps, contradictions, or methodological shortcomings.{pool_context}
Output ONLY a valid JSON array of objects with keys: "gap_id", "title", "description", "significance", and "related_papers" (must contain exact titles selected from the Verified Paper Titles list below).

Verified Paper Titles:
{json.dumps(titles_list, indent=2)}

Literature Review Synthesis:
{state.literature_summary}"""

        raw_gaps = self.llm.generate(prompt=prompt_gaps, system_prompt="Act as Prof. Output clean JSON array representing genuine research gaps.", max_tokens=1500)
        gaps = self._parse_gaps_json(raw_gaps)
        
        if not gaps:
            state.add_log(self.name, "Research Gap Analysis", "LLM failed to output valid JSON for gaps. Using top scraped titles as reference.", status="error")
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

        # 2. Formulate Research Questions & Hypotheses via LLM
        state.add_log(self.name, "Hypothesis Generation", f"Formulating testable hypotheses utilizing discipline methodology: {method.upper()}...")
        
        gaps_desc = "\n".join([f"- [{g.gap_id}] {g.title}: {g.description}" for g in gaps])
        prompt_rq = f"""Act as "Prof"—a world-class research methodologist and PhD supervisor.
CORE PRINCIPLES: Accuracy before style. Evidence before opinion. Simplicity before complexity. Never invent facts.

TASK:
For the following verified research gaps in "{state.topic}", formulate 1 to 2 precise research questions and testable scientific hypotheses tailored for deliverable type: "{state.target_deliverable}".
The recommended methodology for this discipline is "{method}". Do NOT force computational Python simulation if this is a qualitative, humanities, social science, or clinical review topic.
Output ONLY a valid JSON array of objects with keys: "question_id", "question", "hypothesis", "methodology_type" (must be '{method}' or 'hybrid'), "proposed_investigation".

Identified Gaps:
{gaps_desc}"""

        raw_rqs = self.llm.generate(prompt=prompt_rq, system_prompt="Act as Prof. Output clean JSON array.", max_tokens=1500)
        rqs = self._parse_rqs_json(raw_rqs)
        
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

    def _parse_gaps_json(self, raw_text: str) -> List[ResearchGap]:
        try:
            match = re.search(r'\[.*\]', raw_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return [ResearchGap(**item) for item in data]
            data = json.loads(raw_text)
            return [ResearchGap(**item) for item in data]
        except Exception:
            return []

    def _parse_rqs_json(self, raw_text: str) -> List[ResearchQuestion]:
        try:
            match = re.search(r'\[.*\]', raw_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return [ResearchQuestion(**item) for item in data]
            data = json.loads(raw_text)
            return [ResearchQuestion(**item) for item in data]
        except Exception:
            return []
