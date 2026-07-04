"""
v5 Peer Review Board — Editor + 5 specialist reviewers enforcing Q1/Q2 standards.
Can loop back to revision if standards are not met.
"""

import json
from typing import Dict, List, Any
from dataclasses import dataclass, field

from research_engine.models import ResearchState
from research_engine.llm_client import LocalLLMClient


@dataclass
class ReviewDecision:
    reviewer: str
    verdict: str      # ACCEPT, MINOR_REVISION, MAJOR_REVISION, REJECT
    score: float      # 0.0 - 1.0
    comments: str
    specific_issues: List[str] = field(default_factory=list)


class PeerReviewerAgent:
    """Individual reviewer with a specific focus area."""

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
{paper_text[:10000]}
---

Provide your review in this exact JSON format:
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
        try:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                data = json.loads(raw[start:end+1])
            else:
                data = json.loads(raw.strip().strip("`").replace("json", "").strip())
        except Exception:
            data = {"verdict": "MAJOR_REVISION", "score": 0.5, "comments": raw[:1000], "specific_issues": ["JSON parse error — manual review needed."]}

        decision = ReviewDecision(
            reviewer=self.name,
            verdict=data.get("verdict", "MAJOR_REVISION"),
            score=float(data.get("score", 0.5)),
            comments=data.get("comments", ""),
            specific_issues=data.get("specific_issues", []),
        )
        if state:
            state.add_log(self.name, f"Peer Review Round {review_round}", f"Verdict: {decision.verdict}, Score: {decision.score}")
        return decision


class EditorAgent:
    """Chief Editor who aggregates reviews and makes final publication decision."""

    def __init__(self, llm_client: LocalLLMClient):
        self.name = "EditorAgent"
        self.llm = llm_client

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

Synthesize these into a final editorial decision. Provide JSON:
{{
  "editorial_verdict": "ACCEPT|MINOR_REVISION|MAJOR_REVISION|REJECT",
  "overall_score": <float>,
  "letter_to_authors": "<detailed guidance paragraph>",
  "must_address": ["critical issue 1", "critical issue 2"],
  "optional_suggestions": ["optional suggestion 1"]
}}
"""
        raw = self.llm.generate(prompt, system, max_tokens=2200)
        try:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                data = json.loads(raw[start:end+1])
            else:
                data = json.loads(raw.strip().strip("`").replace("json", "").strip())
        except Exception:
            data = {
                "editorial_verdict": "MAJOR_REVISION",
                "overall_score": 0.5,
                "letter_to_authors": raw[:1500],
                "must_address": ["Parse error — manual review needed."],
                "optional_suggestions": [],
            }

        if state:
            state.add_log(self.name, f"Editorial Decision Round {review_round}", f"Verdict: {data['editorial_verdict']}, Score: {data['overall_score']}")
        return data


class PeerReviewBoard:
    """Full board: Editor + 5 Reviewers."""

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

        verdict = editorial["editorial_verdict"]
        if verdict == "ACCEPT" and avg_score < 0.75:
            verdict = "MINOR_REVISION"  # editorial override safety

        return {
            "round": review_round,
            "reviewer_decisions": decisions,
            "editorial": editorial,
            "average_score": avg_score,
            "final_verdict": verdict,
            "must_address": editorial.get("must_address", []),
            "letter_to_authors": editorial.get("letter_to_authors", ""),
        }
