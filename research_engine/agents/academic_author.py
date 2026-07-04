from research_engine.models import ResearchState
from research_engine.llm_client import LocalLLMClient
from research_engine.domain_engine import DomainIntelligenceEngine


class AcademicAuthorAgent:
    """Agent responsible for writing publication-grade deliverables under strict 'Prof' academic standards."""
    def __init__(self, llm_client: LocalLLMClient):
        self.llm = llm_client
        self.name = "Academic Author & Journal Editor-in-Chief"

    def execute(self, state: ResearchState) -> ResearchState:
        state.add_log(self.name, "Manuscript Drafting", f"Synthesizing research artifacts into deliverable: '{state.target_deliverable}'...", f"Topic: '{state.topic}'")
        
        disc, method, _ = DomainIntelligenceEngine.classify_domain_and_methodology(state.topic)
        
        # Build verified citations list
        cits_str = ""
        for i, p in enumerate(state.extracted_papers[:25]):
            year = p.published_date[:4] if p.published_date else "Recent"
            cits_str += f"{i+1}. {p.authors[0] if p.authors else 'Anon'} et al. ({year}). *{p.title}*. {p.source}. Citations: {p.citation_count}\n"

        sim_summary = "No investigation recorded."
        sim_stdout = ""
        if state.simulation_results:
            sim = state.simulation_results[0]
            sim_summary = f"Status: {'SUCCESS' if sim.success else 'FAILED'}\nSummary: {sim.summary_findings}"
            sim_stdout = sim.stdout or ""

        # Pool Document Integration
        pool_instructions = ""
        if state.uploaded_files_content:
            pool_instructions = f"\nCRITICAL RESEARCH POOL DIRECTIVE: The user has uploaded document(s) into the Research Pool. You must execute action: '{state.pool_action}'. Analyze their draft, think deeply with/against their arguments, corroborate assertions using the scraped citations below, and weave their core concepts into this deliverable.\n"

        # Dynamically structure instructions based on Target Deliverable
        deliv = state.target_deliverable.lower()
        if "proposal" in deliv or "grant" in deliv:
            structure_mandate = """Mandatory Proposal Structure:
# Title & Author Block (Target Deliverable: Grant / Research Proposal)
## Executive Summary & Specific Aims
## 1. Research Strategy & Contextual Significance
## 2. Comprehensive Bibliometric Synthesis & Scraped Evidence (Cite specific papers)
## 3. Preliminary Data & Identification of Critical Gap
## 4. Proposed Methodological Framework & Investigation Protocol
## 5. Expected Outcomes, Impact, and Potential Pitfalls
## 6. Project Timeline & Milestone Schedule
## Rigorous Academic References (List all cited works from Scraped Literature)"""
        elif "thesis" in deliv or "chapter" in deliv:
            structure_mandate = """Mandatory Thesis Chapter Structure:
# Chapter Title: Comprehensive Methodological & Theoretical Investigation of the Domain
## Chapter Abstract & Core Contributions
## 1. Introduction & Theoretical Framing
## 2. Exhaustive Review of Contemporary Literature (Deep citation synthesis)
## 3. Scientific Contradictions and Methodological Limitations
## 4. Formal Research Questions and Hypotheses Formulation
## 5. Research Design and Methodological Execution
## 6. Synthesis of Empirical Findings and Methodological Audit
## 7. Deep Analytical Discussion & Implications for Future Chapters
## 8. Chapter Summary & Conclusion
## Exhaustive Academic References"""
        elif "review" in deliv or "prisma" in deliv:
            structure_mandate = """Mandatory Systematic Review Structure:
# Title: Systematic Literature Review and Evidence Synthesis of the Domain
## Abstract (PRISMA Structured)
## 1. Introduction & Rationale for Systematic Review
## 2. PRISMA Methodology (Search strategy across OpenAlex, ArXiv, Semantic Scholar, Crossref; Inclusion/Exclusion criteria)
## 3. Bibliometric Landscape & Citation Impact Analysis
## 4. Thematic Evidence Extraction Matrix (Tabular comparison of scraped works)
## 5. Critical Contradictions, Methodological Biases, and Gaps
## 6. Synthesis of Findings & Framework Proposal
## 7. Limitations of Current Evidence & Future Research Roadmap
## 8. Conclusion
## Verified Systematic References"""
        elif "abstract" in deliv or "summary" in deliv:
            structure_mandate = """Mandatory Abstract & Outline Structure:
# Executive Research Outline & Extended Abstract
## 1. Structured Abstract (Background, Problem, Methods, Results, Conclusion - 400 words)
## 2. Key Scientific Contradictions & Literature Gaps (Citing scraped works)
## 3. Proposed Methodological Protocol
## 4. Expected Impact & Academic Contribution
## References"""
        elif "critique" in deliv or "rebuttal" in deliv:
            structure_mandate = """Mandatory Critique & Rebuttal Structure:
# Scientific Peer Review Critique & Formal Rebuttal Deliverable
## 1. Executive Editorial Summary & Overall Evaluation
## 2. Major Methodological & Theoretical Concerns (Citing counter-evidence from scraped literature)
## 3. Specific Point-by-Point Critique & Actionable Recommendations
## 4. Evaluation of Scientific Rigor and Citation Integrity
## 5. Final Rebuttal / Revision Roadmap
## Cited Reference Evidence"""
        else:
            structure_mandate = """Mandatory Research Manuscript Structure:
# Title & Author Block
## Abstract (250 words, structured: Background, Methods, Results, Conclusion)
## 1. Introduction & Contextual Background
## 2. Comprehensive Related Work & Bibliometric Synthesis (Cite specific scraped papers)
## 3. Identification of the Research Gap
## 4. Formal Research Question & Hypothesis
## 5. Methodology & Investigation Design
## 6. Empirical Findings & Evidence Synthesis (Incorporate tables and data from investigation)
## 7. Rigorous Academic Discussion & Operational Implications
## 8. Conclusion
## Rigorous Academic References (List all cited works from Scraped Literature)"""

        prompt = f"""Act as "Prof"—a world-class interdisciplinary academic with the combined expertise of: Full Professor, Journal Editor-in-Chief, Scientific Reviewer, Technical Writer, Academic Copy Editor, and Scientific Argumentation Expert.
Operate at the level expected by top international journals and leading universities.

CORE PRINCIPLES
1. Accuracy before style. 2. Evidence before opinion. 3. Precision before completeness. 4. Simplicity before complexity. 5. Never use unnecessary words. 6. Never invent facts, citations, results, or references. 7. State uncertainty explicitly when evidence is insufficient. 8. Every sentence must contribute value.

WRITING STYLE
Write like an experienced human academic.
The writing must be: natural, concise, direct, readable, professional, publication-ready.
Avoid: AI-style wording, generic transitions, exaggerated claims, repetitive phrases, motivational language, unnecessary adjectives, verbose explanations, filler, clichés ("delve into", "tapestry", "testament", "moreover", "in conclusion").
Prefer: short paragraphs, active voice, precise terminology, logical progression, strong topic sentences, clean argumentation (Claim -> Evidence -> Reasoning -> Limitations -> Conclusion).

TASK:
Draft a complete, publication-ready academic deliverable formatted in clean Markdown (.md) for: "{state.topic}" (Discipline: {disc}).
Target Deliverable Format & Length: "{state.target_deliverable}".{pool_instructions}

CRITICAL MANDATES:
1. Every claim MUST be backed by an explicit in-text academic citation (e.g., (Smith et al., 2024; Vance, 2025)) drawing strictly from the Scraped Literature list below. Do not make unsupported assertions or invent citations.
2. The investigation methodology is "{method.upper()}". Tailor your methodology and analysis sections strictly to this paradigm. Do not invent Python code simulations if this is a qualitative, legal, social science, or clinical study.

{structure_mandate}

--- SCRAPED LITERATURE CONTEXT ---
{cits_str}
----------------------------------
Literature Review Synthesis:
{state.literature_summary}

Target Research Gap:
{state.identified_gaps[0].title if state.identified_gaps else 'None'}
{state.identified_gaps[0].description if state.identified_gaps else ''}

Scientific Hypothesis:
{state.research_questions[0].hypothesis if state.research_questions else 'None'}

Investigation Output:
{sim_summary}
{sim_stdout[:1800]}"""

        system_prompt = "Act as Prof. World-class academic rigor. Zero filler, zero invented facts, strict citation adherence."
        manuscript = self.llm.generate(prompt=prompt, system_prompt=system_prompt, max_tokens=4000)
        
        if not manuscript or "[LLM ENGINE OFFLINE" in manuscript or "[Ollama API Error]" in manuscript:
            state.add_log(self.name, "Manuscript Drafting", "LLM engine error encountered during manuscript generation.", status="error")
            
        state.final_manuscript_md = manuscript
        state.progress_percentage = 100
        state.add_log(self.name, "Manuscript Drafting", "Academic deliverable generated successfully!", status="completed")
        return state
