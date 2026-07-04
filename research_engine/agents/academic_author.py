"""
v5 Academic Author Agent — Chunked long-form generation with quality validation.
Validates each section is non-empty and retries if LLM produces garbage.
"""

import os
import time
import re
from typing import Dict, Any, List, Optional

from research_engine.models import ResearchState
from research_engine.llm_client import LocalLLMClient
from research_engine.domain_engine import DomainIntelligenceEngine


class AcademicAuthorAgent:
    """Agent responsible for writing publication-grade deliverables."""

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

    MIN_SECTION_LENGTH = 200  # Minimum chars for a valid section

    def __init__(self, llm_client: LocalLLMClient):
        self.llm = llm_client
        self.name = "Academic Author & Journal Editor-in-Chief"

    def execute(self, state: ResearchState) -> ResearchState:
        state.add_log(self.name, "Manuscript Drafting", f"Synthesizing research artifacts into deliverable: '{state.target_deliverable}'...", f"Topic: '{state.topic}'")

        disc, method, _ = DomainIntelligenceEngine.classify_domain_and_methodology(state.topic)

        if not state.outline:
            self._build_outline(state, disc)

        self._draft_sections(state, disc, method)

        paper = self._compile_paper(state)
        state.final_manuscript_md = paper
        state.progress_percentage = 100
        state.add_log(self.name, "Manuscript Drafting", "Academic deliverable generated successfully via chunked drafting!", status="completed")
        return state

    def _build_outline(self, state: ResearchState, disc: str):
        system = "You are an academic research architect. Return ONLY a JSON array of strings."
        prompt = f"""
Topic: {state.topic}
Domain: {disc}
Target Deliverable: {state.target_deliverable}

Generate a detailed academic paper outline as a JSON array of strings.
Include 8-12 sections: Abstract, Introduction, Literature Review, Methodology, Results, Discussion, Conclusion, References.

Respond ONLY with raw JSON array (no markdown, no code blocks):
"""
        raw = self.llm.generate(prompt, system, max_tokens=1500)
        data = self.llm.extract_json(raw)
        if data and isinstance(data, list):
            outline = data
        else:
            outline = self.STANDARD_OUTLINE.copy()
            if disc:
                outline.insert(3, f"{disc} Specific Considerations")

        state.outline = outline
        state.add_log(self.name, "Build Outline", f"Outline created with {len(outline)} sections", str(outline))

    def _draft_sections(self, state: ResearchState, disc: str, method: str):
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

        expert_feedback = ""
        if state.expert_reviews:
            expert_feedback = "\nExpert Feedback to Address:\n" + "\n".join(
                f"- {e.expert_name}: {e.suggestions[:2] if e.suggestions else 'No suggestions'}"
                for e in state.expert_reviews
            )

        peer_feedback = ""
        if state.peer_reviews:
            peer_feedback = "\nPeer Review Issues to Address:\n" + "\n".join(
                f"- {r.reviewer}: {r.specific_issues[:2] if r.specific_issues else 'No issues'}"
                for r in state.peer_reviews
            )

        previous_text = f"# {state.topic}\n\n"
        state.sections = {}

        for idx, section in enumerate(state.outline):
            content = None
            attempts = 0
            max_attempts = 2

            while (content is None or len(content) < self.MIN_SECTION_LENGTH) and attempts < max_attempts:
                attempts += 1
                state.add_log(self.name, f"Draft Section {idx+1}/{len(state.outline)}", f"Writing: {section} (attempt {attempts})")

                system = (
                    "You are an elite academic writer. Produce publication-ready prose. "
                    "Cite prior work naturally. Use precise terminology. Avoid filler. "
                    "Write ONLY the requested section."
                )

                prompt = self._build_section_prompt(
                    title=state.topic,
                    section=section,
                    section_index=idx,
                    total_sections=len(state.outline),
                    previous_summary=previous_text[-2500:],
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
                quality = self.llm.validate_quality(content, min_length=self.MIN_SECTION_LENGTH)
                if not quality["has_content"]:
                    state.add_log(self.name, f"Draft Section {idx+1}/{len(state.outline)}", f"WARNING: Section too short ({len(content)} chars). Retrying...", status="warning")
                    content = None

            if content is None or len(content) < self.MIN_SECTION_LENGTH:
                content = f"\n\n*[Section '{section}' could not be generated due to LLM limitations. Please use a more powerful model or increase context window.]*\n\n"
                state.add_log(self.name, f"Draft Section {idx+1}/{len(state.outline)}", f"FAILED: Section '{section}' could not be generated.", status="error")

            state.sections[section] = content
            previous_text += f"\n\n## {section}\n\n{content}\n"

            state.progress_percentage = 50 + int((idx + 1) / len(state.outline) * 45)
            state.add_log(self.name, f"Draft Section {idx+1}/{len(state.outline)}", f"Completed: {section} ({len(content)} chars)", status="completed")

    def _build_section_prompt(self, title: str, section: str, section_index: int, total_sections: int,
                               previous_summary: str, citations: str, literature_summary: str,
                               gap: str, hypothesis: str, simulation: str, pool: str,
                               expert_feedback: str, peer_feedback: str, disc: str, method: str,
                               target_deliverable: str) -> str:
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
        if not state.peer_reviews:
            return state.final_manuscript_md

        paper = self._compile_paper(state)
        must_address = []
        for r in state.peer_reviews:
            must_address.extend(r.specific_issues)
        must_address = list(set(must_address))[:10]

        if not must_address:
            return paper

        issues_text = "\n".join(f"- {issue}" for issue in must_address)
        system = "You are an author revising a paper based on strict peer review feedback."
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
        self._update_sections_from_markdown(state, revised)
        state.final_manuscript_md = revised
        return revised

    def _update_sections_from_markdown(self, state: ResearchState, markdown: str):
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
