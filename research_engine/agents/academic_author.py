"""
v5 Academic Author Agent — Chunked long-form generation to prevent local model context collapse.
Drafts papers section-by-section with memory and expert feedback integration.
"""

import os
import time
import re
from typing import Dict, Any, List, Optional

from research_engine.models import ResearchState
from research_engine.llm_client import LocalLLMClient
from research_engine.domain_engine import DomainIntelligenceEngine


class AcademicAuthorAgent:
    """Agent responsible for writing publication-grade deliverables under strict 'Prof' academic standards.
    v5: Uses chunked section drafting to respect local LLM context limits."""

    STANDARD_OUTLINE = [
        "Abstract",
        "Introduction",
        "Literature Review",
        "Theoretical Framework",
        "Methodology",
        "Results",
        "Discussion",
        "Conclusion",
        "References",
    ]

    def __init__(self, llm_client: LocalLLMClient):
        self.llm = llm_client
        self.name = "Academic Author & Journal Editor-in-Chief"

    def execute(self, state: ResearchState) -> ResearchState:
        state.add_log(self.name, "Manuscript Drafting", f"Synthesizing research artifacts into deliverable: '{state.target_deliverable}'...", f"Topic: '{state.topic}'")

        disc, method, _ = DomainIntelligenceEngine.classify_domain_and_methodology(state.topic)

        # v5: Build outline if not already present
        if not state.outline:
            self._build_outline(state, disc)

        # v5: Chunked section drafting
        self._draft_sections(state, disc, method)

        # Compile final paper
        paper = self._compile_paper(state)
        state.final_manuscript_md = paper
        state.progress_percentage = 100
        state.add_log(self.name, "Manuscript Drafting", "Academic deliverable generated successfully via chunked drafting!", status="completed")
        return state

    def _build_outline(self, state: ResearchState, disc: str):
        system = "You are an academic research architect. Design a rigorous paper outline. Return ONLY a JSON array of strings."
        prompt = f"""
Topic: {state.topic}
Domain: {disc}
Target Deliverable: {state.target_deliverable}

Generate a detailed academic paper outline as a JSON array of strings.
Each string should be a major section title. Include 8-12 sections.
Include: Abstract, Introduction, Literature Review, Methodology, Results, Discussion, Conclusion, References.
Add domain-specific sections if needed.

Output ONLY JSON array.
"""
        raw = self.llm.generate(prompt, system, max_tokens=1500)
        try:
            import json
            start = raw.find("[")
            end = raw.rfind("]")
            if start != -1 and end != -1:
                outline = json.loads(raw[start:end+1])
            else:
                outline = json.loads(raw.strip().strip("`").replace("json", "").strip())
            if not isinstance(outline, list):
                raise ValueError
        except Exception:
            outline = self.STANDARD_OUTLINE.copy()
            if disc:
                outline.insert(3, f"{disc} Specific Considerations")

        state.outline = outline
        state.add_log(self.name, "Build Outline", f"Outline created with {len(outline)} sections", str(outline))

    def _draft_sections(self, state: ResearchState, disc: str, method: str):
        """v5: Draft each section independently to avoid context collapse."""
        cits_str = ""
        for i, p in enumerate(state.extracted_papers[:25]):
            year = p.published_date[:4] if p.published_date else "Recent"
            cits_str += f"{i+1}. {p.authors[0] if p.authors else 'Anon'} et al. ({year}). *{p.title}*. {p.source}.\n"

        sim_summary = "No investigation recorded."
        if state.simulation_results:
            sim = state.simulation_results[0]
            sim_summary = f"Status: {'SUCCESS' if sim.success else 'FAILED'}\nSummary: {sim.summary_findings}"

        pool_instructions = ""
        if state.uploaded_files_content:
            pool_instructions = f"\nCRITICAL: User uploaded documents. Action: '{state.pool_action}'. Integrate their arguments.\n"

        # Expert feedback for revision rounds
        expert_feedback = ""
        if state.expert_reviews:
            expert_feedback = "\nExpert Feedback to Address:\n" + "\n".join(
                f"- {e.expert_name}: {e.suggestions[:2] if e.suggestions else 'No suggestions'}"
                for e in state.expert_reviews
            )

        # Peer review feedback for revision
        peer_feedback = ""
        if state.peer_reviews:
            peer_feedback = "\nPeer Review Issues to Address:\n" + "\n".join(
                f"- {r.reviewer}: {r.specific_issues[:2] if r.specific_issues else 'No issues'}"
                for r in state.peer_reviews
            )

        previous_text = f"# {state.topic}\n\n"
        state.sections = {}

        for idx, section in enumerate(state.outline):
            state.add_log(self.name, f"Draft Section {idx+1}/{len(state.outline)}", f"Writing: {section}")

            system = (
                "You are an elite academic writer. Produce publication-ready prose. "
                "Cite prior work naturally. Use precise terminology. Avoid filler. "
                "Write ONLY the requested section."
            )

            # Build section-specific prompt with limited context
            prompt = self._build_section_prompt(
                title=state.topic,
                section=section,
                section_index=idx,
                total_sections=len(state.outline),
                previous_summary=previous_text[-2500:],  # keep last ~2500 chars as context
                citations=cits_str,
                literature_summary=state.literature_summary[:2000],
                gap=state.identified_gaps[0].title if state.identified_gaps else "None",
                hypothesis=state.research_questions[0].hypothesis if state.research_questions else "None",
                simulation=sim_summary,
                pool=pool_instructions,
                expert_feedback=expert_feedback,
                peer_feedback=peer_feedback,
                disc=disc,
                method=method,
                target_deliverable=state.target_deliverable,
            )

            content = self.llm.generate(prompt, system, max_tokens=3000)
            state.sections[section] = content
            previous_text += f"\n\n## {section}\n\n{content}\n"

            state.progress_percentage = 50 + int((idx + 1) / len(state.outline) * 45)
            state.add_log(self.name, f"Draft Section {idx+1}/{len(state.outline)}", f"Completed: {section}", status="completed")

    def _build_section_prompt(self, title: str, section: str, section_index: int, total_sections: int,
                               previous_summary: str, citations: str, literature_summary: str,
                               gap: str, hypothesis: str, simulation: str, pool: str,
                               expert_feedback: str, peer_feedback: str, disc: str, method: str,
                               target_deliverable: str) -> str:
        """Construct a focused prompt for a single section."""

        word_guide = {
            "Abstract": "200-400 words",
            "Conclusion": "300-500 words",
            "References": "List format only",
        }.get(section, "800-1500 words")

        return f"""You are writing an academic deliverable titled: "{title}" (Discipline: {disc}).

This is Section {section_index + 1} of {total_sections}: "{section}".
Target Deliverable: {target_deliverable}

Write ONLY this section. Do not write other sections. Aim for {word_guide}.

Context from previous sections (last part):
---
{previous_summary}
---

Verified Citations (use these, do not invent):
{citations}

Literature Synthesis Summary:
{literature_summary}

Research Gap: {gap}
Hypothesis: {hypothesis}
Investigation Output: {simulation}
{pool}
{expert_feedback}
{peer_feedback}

Methodology: {method.upper()}

Rules:
1. Every claim MUST be backed by an explicit in-text citation (e.g., (Smith et al., 2024)).
2. Do not invent citations — use only from the provided list.
3. Use Markdown formatting.
4. Be thorough, evidence-based, and academically rigorous.
5. State uncertainty explicitly when evidence is insufficient.
"""

    def _compile_paper(self, state: ResearchState) -> str:
        parts = [f"# {state.topic}\n"]
        for section in state.outline:
            if section in state.sections:
                parts.append(f"\n## {section}\n\n{state.sections[section]}\n")
        return "\n".join(parts)

    def revise_for_peer_review(self, state: ResearchState) -> str:
        """v5: Revise compiled paper based on peer review feedback."""
        if not state.peer_reviews:
            return state.final_manuscript_md

        paper = self._compile_paper(state)
        must_address = []
        for r in state.peer_reviews:
            must_address.extend(r.specific_issues)
        must_address = list(set(must_address))[:10]  # deduplicate and limit

        if not must_address:
            return paper

        issues_text = "\n".join(f"- {issue}" for issue in must_address)
        system = "You are an author revising a paper based on strict peer review feedback. Address every issue."
        prompt = f"""
Revise the following paper based on critical peer review issues.

Issues to Address:
{issues_text}

Current Paper:
{paper[:12000]}

Produce the full revised paper in Markdown. Address every issue systematically.
Preserve structure. Improve clarity, evidence, and rigor.
"""
        revised = self.llm.generate(prompt, system, max_tokens=4000)
        # Re-parse sections
        self._update_sections_from_markdown(state, revised)
        state.final_manuscript_md = revised
        return revised

    def _update_sections_from_markdown(self, state: ResearchState, markdown: str):
        """Re-parse sections after revision."""
        sections = {}
        current = None
        buffer = []
        for line in markdown.splitlines():
            m = re.match(r"^##\s+(.+)$", line)
            if m:
                if current:
                    sections[current] = "\n".join(buffer).strip()
                current = m.group(1).strip()
                buffer = []
            elif current:
                buffer.append(line)
        if current:
            sections[current] = "\n".join(buffer).strip()
        state.sections.update(sections)

    def save_paper(self, state: ResearchState, output_dir: str = "./sample_outputs") -> str:
        os.makedirs(output_dir, exist_ok=True)
        safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in state.topic)
        filename = f"{safe_title}_{int(time.time())}.md"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(state.final_manuscript_md)
        state.add_log(self.name, "Save Paper", f"Saved to {filepath}")
        return filepath
