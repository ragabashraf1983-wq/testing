"""
v5 Domain Expert Council — 7 specialist agents with robust JSON extraction.
Falls back to text-based scoring if LLM fails structured JSON.
"""

import json
import re
from typing import Dict, List, Any
from dataclasses import dataclass, field

from research_engine.models import ResearchState
from research_engine.llm_client import LocalLLMClient


@dataclass
class ExpertReview:
    expert_name: str
    domain: str
    score: float
    confidence: float
    criticisms: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    endorsements: List[str] = field(default_factory=list)
    dissent: bool = False
    dissent_reason: str = ""


class DomainExpertAgent:
    EXPERTS_CONFIG = [
        {"name": "LinguistExpert", "persona": "Senior Professor of Linguistics and Technical Writing",
         "focus": ["grammar", "style", "clarity", "readability", "terminology", "narrative flow"], "weight": 1.0},
        {"name": "MathematicianExpert", "persona": "Pure and Applied Mathematics Professor",
         "focus": ["proofs", "statistical validity", "numerical accuracy", "modeling", "derivations"], "weight": 1.0},
        {"name": "PhysicistExpert", "persona": "Theoretical and Experimental Physicist",
         "focus": ["laws", "units", "experimental design", "physical consistency", "simulation"], "weight": 1.0},
        {"name": "StatisticianExpert", "persona": "Biostatistics and Data Science Professor",
         "focus": ["significance", "p-values", "confidence intervals", "dataset validity", "bias"], "weight": 1.0},
        {"name": "MethodologistExpert", "persona": "Research Methodology Professor",
         "focus": ["study design", "sampling", "reproducibility", "ethics", "framework alignment"], "weight": 1.0},
        {"name": "LogisticianExpert", "persona": "Operations Research and Systems Analyst",
         "focus": ["resource constraints", "feasibility", "timelines", "logistics", "scalability"], "weight": 1.0},
        {"name": "EpistemologistExpert", "persona": "Philosophy of Science Scholar",
         "focus": ["logical consistency", "epistemic validity", "assumptions", "falsifiability"], "weight": 1.0},
    ]

    def __init__(self, name: str, persona: str, focus_areas: List[str], weight: float, llm_client: LocalLLMClient):
        self.name = name
        self.persona = persona
        self.focus_areas = focus_areas
        self.weight = weight
        self.llm = llm_client

    def _parse_text_fallback(self, raw: str) -> ExpertReview:
        """If JSON fails, extract scores/verdicts from free text."""
        score = 0.5
        confidence = 0.5
        dissent = False
        criticisms = []
        suggestions = []
        endorsements = []
        dissent_reason = ""

        # Try to find score patterns
        score_match = re.search(r'score[:\s=]+(\d+(?:\.\d+)?)', raw, re.I)
        if score_match:
            score = float(score_match.group(1))

        conf_match = re.search(r'confidence[:\s=]+(\d+(?:\.\d+)?)', raw, re.I)
        if conf_match:
            confidence = float(conf_match.group(1))

        if re.search(r'\bdissent\b[:\s=]*true', raw, re.I):
            dissent = True

        # Extract bullet points as criticisms/suggestions
        for line in raw.split('\n'):
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                item = line[2:]
                if any(w in item.lower() for w in ['criticism', 'flaw', 'weak', 'problem', 'error', 'issue']):
                    criticisms.append(item)
                elif any(w in item.lower() for w in ['suggest', 'improve', 'recommend', 'should', 'could']):
                    suggestions.append(item)
                elif any(w in item.lower() for w in ['endorse', 'agree', 'strength', 'correct', 'valid']):
                    endorsements.append(item)

        return ExpertReview(
            expert_name=self.name,
            domain=self.persona,
            score=min(1.0, max(0.0, score)),
            confidence=min(1.0, max(0.0, confidence)),
            criticisms=criticisms or ["LLM failed to produce structured JSON. Fallback parsing used."],
            suggestions=suggestions or ["Consider using a stronger LLM model for better evaluation."],
            endorsements=endorsements,
            dissent=dissent,
            dissent_reason=dissent_reason,
        )

    def evaluate(self, content: str, context: str = "") -> ExpertReview:
        system = f"You are {self.persona}. Your expertise covers: {', '.join(self.focus_areas)}. Be critical. Do NOT agree automatically."
        prompt = f"""
Evaluate the following research content from your specialist perspective.

Context: {context}

Content to evaluate:
---
{content[:8000]}
---

Provide your evaluation in this EXACT JSON format (no markdown, no code blocks, raw JSON only):
{{
  "score": <float 0.0-1.0>,
  "confidence": <float 0.0-1.0>,
  "criticisms": ["specific criticism 1", "specific criticism 2"],
  "suggestions": ["specific suggestion 1", "specific suggestion 2"],
  "endorsements": ["specific endorsement 1"],
  "dissent": <true or false>,
  "dissent_reason": "<reason if dissenting>"
}}

Rules:
- Be critical. Do NOT agree automatically. Identify real flaws.
- If the content violates principles in your domain, mark dissent=true.
- Suggest concrete improvements, not generic praise.
"""
        raw = self.llm.generate(prompt, system, max_tokens=2200)

        # Try robust JSON extraction first
        data = self.llm.extract_json(raw)
        if data is None or data.get("_parse_error"):
            # Fallback to text parsing
            return self._parse_text_fallback(raw)

        return ExpertReview(
            expert_name=self.name,
            domain=self.persona,
            score=float(data.get("score", 0.5)),
            confidence=float(data.get("confidence", 0.5)),
            criticisms=data.get("criticisms", []) or ["No criticisms provided."],
            suggestions=data.get("suggestions", []) or ["No suggestions provided."],
            endorsements=data.get("endorsements", []),
            dissent=data.get("dissent", False),
            dissent_reason=data.get("dissent_reason", ""),
        )


class DomainExpertCouncil:
    def __init__(self, llm_client: LocalLLMClient):
        self.experts: List[DomainExpertAgent] = []
        for ecfg in DomainExpertAgent.EXPERTS_CONFIG:
            self.experts.append(DomainExpertAgent(
                name=ecfg["name"],
                persona=ecfg["persona"],
                focus_areas=ecfg["focus"],
                weight=ecfg["weight"],
                llm_client=llm_client,
            ))

    def evaluate(self, content: str, context: str = "", state: ResearchState = None) -> Dict[str, Any]:
        reviews: List[ExpertReview] = []
        for expert in self.experts:
            review = expert.evaluate(content, context)
            reviews.append(review)
            if state:
                state.add_log(expert.name, "Expert Evaluation", f"Score: {review.score}, Dissent: {review.dissent}", f"Criticisms: {len(review.criticisms)}")

        dissenters = [r for r in reviews if r.dissent]
        total_conf = sum(r.confidence for r in reviews)
        avg_score = sum(r.score * r.confidence for r in reviews) / max(total_conf, 0.001)
        consensus = 1.0 - (len(dissenters) / max(len(reviews), 1))

        all_criticisms = []
        all_suggestions = []
        for r in reviews:
            all_criticisms.extend(r.criticisms)
            all_suggestions.extend(r.suggestions)

        # Detect LLM failure pattern: all scores identical to 0.5
        scores = [r.score for r in reviews]
        llm_failure = len(set(scores)) == 1 and scores[0] == 0.5

        return {
            "reviews": reviews,
            "average_score": avg_score,
            "consensus_level": consensus,
            "dissent_count": len(dissenters),
            "dissenters": [r.expert_name for r in dissenters],
            "consolidated_criticisms": all_criticisms,
            "consolidated_suggestions": all_suggestions,
            "llm_failure_detected": llm_failure,
        }
