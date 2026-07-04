"""
v5 Peer Review Board — Editor + 5 specialist reviewers enforcing Q1/Q2 standards.
Robust JSON extraction with LLM failure detection.
"""

import re
from typing import Dict, List, Any
from dataclasses import dataclass, field

from research_engine.models import ResearchState
from research_engine.llm_client import LocalLLMClient


@dataclass
class ReviewDecision:
    reviewer: str
    verdict: str      # ACCEPT, MINOR_REVISION, MAJOR_REVISION, REJECT
    score: float
    comments: str
    specific_issues: List[str] = field(default_factory=list)


class PeerReviewerAgent:
    REVIEWERS_CONFIG = [
        {"name": "MethodologyReviewer", "focus": ["study_design", "data_collection", "reproducibility", "ethical_compliance"]},
        {"name": "LiteratureReviewer", "focus": ["citation_depth", "gap_analysis", "prior_work_alignment", "scholarship"]},
        {"name": "ResultsReviewer", "focus": ["result_validity", "statistical_rigor", "figure_table_quality", "interpretation"]},
        {"name": "ImpactReviewer", "focus": ["practical_applicability", "societal_value", "interdisciplinary_relevance"]},
        {"name": "NoveltyReviewer", "focus": ["originality", "contribution_magnitude", "theoretical_advancement"]},
    ]

    def __init__(self, name: str, focus: List[str], llm_client: LocalLLMClient):
        self.name = name
        self.focus = focus
        self.llm = llm_client

    def _parse_text_fallback(self, raw: str) -> ReviewDecision:
        """Extract verdict and score from free text if JSON fails."""
        score = 0.5
        verdict = "MAJOR_REVISION"
        comments = raw[:1500]
        issues = []

        # Score extraction
        score_match = re.search(r'score[:\s=]+(\d+(?:\.\d+)?)', raw, re.I)
        if score_match:
            score = float(score_match.group(1))

        # Verdict extraction
        if re.search(r'\bACCEPT\b', raw, re.I):
            verdict = "ACCEPT"
        elif re.search(r'\bMINOR_REVISION\b', raw, re.I):
            verdict = "MINOR_REVISION"
        elif re.search(r'\bMAJOR_REVISION\b', raw, re.I):
            verdict = "MAJOR_REVISION"
        elif re.search(r'\bREJECT\b', raw, re.I):
            verdict = "REJECT"

        # Issues from bullets
        for line in raw.split('\n'):
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                issues.append(line[2:])

        return ReviewDecision(
            reviewer=self.name,
            verdict=verdict,
            score=min(1.0, max(0.0, score)),
            comments=comments,
            specific_issues=issues or ["LLM failed to produce structured JSON. Fallback parsing used."],
        )

    def review(self, paper_text: str, review_round: int, state: ResearchState = None) -> ReviewDecision:
        system = (
            f"You are a rigorous academic peer reviewer specializing in: {', '.join(self.focus)}. "
            "You evaluate papers for Q1/Q2 journal standards (Nature/Science/IEEE/ACM tier). Be brutally honest. "
            "Do not accept substandard work."
        )
        prompt = f"""
Round: {review_round}

Review the following paper draft from your specialist perspective ({', '.join(self.focus)}).

Paper Draft:
---
{paper_text[:8000]}
---

Provide your review in this EXACT JSON format (no markdown, no code blocks, raw JSON only):
{{
  "verdict": "ACCEPT|MINOR_REVISION|MAJOR_REVISION|REJECT",
  "score": <float 0.0-1.0>,
  "comments": "<overall assessment paragraph>",
  "specific_issues": ["issue 1", "issue 2", ...]
}}

Verdict rules:
- ACCEPT: Score >= 0.80, no major flaws.
- MINOR_REVISION: Score 0.60-0.79, small fixes needed.
- MAJOR_REVISION: Score 0.40-0.59, fundamental issues.
- REJECT: Score < 0.40, not suitable.
"""
        raw = self.llm.generate(prompt, system, max_tokens=2200)

        data = self.llm.extract_json(raw)
        if data is None or data.get("_parse_error"):
            return self._parse_text_fallback(raw)

        return ReviewDecision(
            reviewer=self.name,
            verdict=data.get("verdict", "MAJOR_REVISION"),
            score=float(data.get("score", 0.5)),
            comments=data.get("comments", ""),
            specific_issues=data.get("specific_issues", []),
        )


class EditorAgent:
    def __init__(self, llm_client: LocalLLMClient):
        self.name = "EditorAgent"
        self.llm = llm_client

    def _parse_text_fallback(self, raw: str) -> Dict[str, Any]:
        score = 0.5
        verdict = "MAJOR_REVISION"
        if re.search(r'\bACCEPT\b', raw, re.I):
            verdict = "ACCEPT"
        elif re.search(r'\bMINOR_REVISION\b', raw, re.I):
            verdict = "MINOR_REVISION"
        elif re.search(r'\bMAJOR_REVISION\b', raw, re.I):
            verdict = "MAJOR_REVISION"
        elif re.search(r'\bREJECT\b', raw, re.I):
            verdict = "REJECT"
        score_match = re.search(r'score[:\s=]+(\d+(?:\.\d+)?)', raw, re.I)
        if score_match:
            score = float(score_match.group(1))
        return {
            "editorial_verdict": verdict,
            "overall_score": score,
            "letter_to_authors": raw[:1500],
            "must_address": ["LLM failed to produce structured JSON. Manual review needed."],
            "optional_suggestions": [],
        }

    def editorial_decision(self, decisions: List[ReviewDecision], review_round: int, state: ResearchState = None) -> Dict[str, Any]:
        system = (
            "You are the Chief Editor of a top-tier Q1 journal (Nature/Science tier). "
            "You synthesize multiple reviewer reports into a final editorial decision. You demand excellence."
        )
        reviews_text = "\n\n".join(
            f"Reviewer: {d.reviewer}\nVerdict: {d.verdict}\nScore: {d.score}\nComments: {d.comments}\nIssues: {d.specific_issues}"
            for d in decisions
        )
        prompt = f"""
Review Round: {review_round}

You have received the following peer reviews:

{reviews_text}

Synthesize these into a final editorial decision. Provide EXACT JSON (no markdown, no code blocks, raw JSON only):
{{
  "editorial_verdict": "ACCEPT|MINOR_REVISION|MAJOR_REVISION|REJECT",
  "overall_score": <float>,
  "letter_to_authors": "<detailed guidance paragraph>",
  "must_address": ["critical issue 1", "critical issue 2"],
  "optional_suggestions": ["optional suggestion 1"]
}}
"""
        raw = self.llm.generate(prompt, system, max_tokens=2200)

        data = self.llm.extract_json(raw)
        if data is None or data.get("_parse_error"):
            data = self._parse_text_fallback(raw)

        if state:
            state.add_log(self.name, f"Editorial Decision Round {review_round}", f"Verdict: {data['editorial_verdict']}, Score: {data['overall_score']}")
        return data


class PeerReviewBoard:
    def __init__(self, llm_client: LocalLLMClient):
        self.editor = EditorAgent(llm_client)
        self.reviewers: List[PeerReviewerAgent] = []
        for rcfg in PeerReviewerAgent.REVIEWERS_CONFIG:
            self.reviewers.append(PeerReviewerAgent(
                name=rcfg["name"],
                focus=rcfg["focus"],
                llm_client=llm_client,
            ))

    def review(self, paper_text: str, review_round: int, state: ResearchState = None) -> Dict[str, Any]:
        decisions = []
        for reviewer in self.reviewers:
            d = reviewer.review(paper_text, review_round, state)
            decisions.append(d)

        editorial = self.editor.editorial_decision(decisions, review_round, state)
        scores = [d.score for d in decisions]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Detect LLM failure: all identical scores
        all_same = len(set(scores)) == 1
        llm_failure = all_same and scores[0] in (0.5, 0.0)

        verdict = editorial["editorial_verdict"]
        if verdict == "ACCEPT" and avg_score < 0.75:
            verdict = "MINOR_REVISION"

        return {
            "round": review_round,
            "reviewer_decisions": decisions,
            "editorial": editorial,
            "average_score": avg_score,
            "final_verdict": verdict,
            "must_address": editorial.get("must_address", []),
            "letter_to_authors": editorial.get("letter_to_authors", ""),
            "llm_failure_detected": llm_failure,
        }
