"""
v5 Domain Expert Council — 7 specialist agents that evaluate from their domain lens
and are encouraged to dissent rather than agree automatically.
"""

import json
from typing import Dict, List, Any
from dataclasses import dataclass, field

from research_engine.models import ResearchState
from research_engine.llm_client import LocalLLMClient


@dataclass
class ExpertReview:
    expert_name: str
    domain: str
    score: float              # 0.0 - 1.0 overall quality
    confidence: float         # 0.0 - 1.0 how sure the expert is
    criticisms: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    endorsements: List[str] = field(default_factory=list)
    dissent: bool = False     # True if expert fundamentally disagrees with direction
    dissent_reason: str = ""


class DomainExpertAgent:
    """A single domain expert with a specific persona."""

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

    def evaluate(self, content: str, context: str = "") -> ExpertReview:
        system = f"You are {self.persona}. Your expertise covers: {', '.join(self.focus_areas)}. Be critical. Do NOT agree automatically."
        prompt = f"""
Evaluate the following research content from your specialist perspective.

Context: {context}

Content to evaluate:
---
{content[:12000]}
---

Provide your evaluation in this exact JSON format:
{{
  "score": <float 0.0-1.0>,
  "confidence": <float 0.0-1.0>,
  "criticisms": ["..."],
  "suggestions": ["..."],
  "endorsements": ["..."],
  "dissent": <true/false>,
  "dissent_reason": "..."
}}

Rules:
- Be critical. Do NOT agree automatically. Identify real flaws.
- If the content violates principles in your domain, mark dissent=true.
- Suggest concrete improvements, not generic praise.
"""
        raw = self.llm.generate(prompt, system, max_tokens=2200)
        try:
            # Try to extract JSON from the response
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                data = json.loads(raw[start:end+1])
            else:
                data = json.loads(raw.strip().strip("`").replace("json", "").strip())
        except Exception:
            data = {
                "score": 0.5, "confidence": 0.5,
                "criticisms": ["JSON parsing failed", raw[:500]],
                "suggestions": [], "endorsements": [],
                "dissent": False, "dissent_reason": ""
            }

        return ExpertReview(
            expert_name=self.name,
            domain=self.persona,
            score=float(data.get("score", 0.5)),
            confidence=float(data.get("confidence", 0.5)),
            criticisms=data.get("criticisms", []),
            suggestions=data.get("suggestions", []),
            endorsements=data.get("endorsements", []),
            dissent=data.get("dissent", False),
            dissent_reason=data.get("dissent_reason", ""),
        )


class DomainExpertCouncil:
    """Orchestrates all domain experts and computes consensus."""

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

        return {
            "reviews": reviews,
            "average_score": avg_score,
            "consensus_level": consensus,
            "dissent_count": len(dissenters),
            "dissenters": [r.expert_name for r in dissenters],
            "consolidated_criticisms": all_criticisms,
            "consolidated_suggestions": all_suggestions,
        }
