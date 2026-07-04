"""
v5 Conflict Resolution Agent — Orchestrates adversarial debates among experts
when consensus is low. Produces weighted resolutions and logs all disagreements.
"""

import json
from typing import Dict, List, Any

from research_engine.models import ResearchState
from research_engine.llm_client import LocalLLMClient


class ConflictResolutionAgent:
    """Resolves expert disagreements through structured debate rounds."""

    def __init__(self, llm_client: LocalLLMClient):
        self.name = "ConflictResolutionAgent"
        self.llm = llm_client

    def debate(self, content: str, expert_reviews: List[Any], topic: str,
               max_rounds: int = 3, consensus_threshold: float = 0.60,
               state: ResearchState = None) -> Dict[str, Any]:
        """Run structured debate rounds until consensus or max rounds reached."""
        dissenters = [r for r in expert_reviews if getattr(r, "dissent", False)]
        if not dissenters:
            if state:
                state.add_log(self.name, "Debate", "All experts in consensus. No debate needed.")
            return {
                "resolved": True, "rounds": 0,
                "final_resolution": "Consensus achieved without debate.",
                "changes_required": [],
                "winning_experts": [],
                "losing_experts": [],
            }

        round_num = 0
        resolution = ""
        changes_required = []
        current_content = content

        while round_num < max_rounds:
            round_num += 1
            if state:
                state.add_log(self.name, f"Debate Round {round_num}", f"Topic: {topic}", f"Dissenters: {[d.expert_name for d in dissenters]}")

            # Build debate prompt from dissenters
            dissent_args = []
            for d in dissenters:
                args = d.criticisms[:3] if hasattr(d, 'criticisms') and d.criticisms else [d.dissent_reason] if hasattr(d, 'dissent_reason') else ["Fundamental disagreement"]
                dissent_args.append(f"Expert {d.expert_name}: {args}")

            system = (
                "You are an impartial arbiter in an academic debate. You weigh arguments by domain validity, "
                "evidence strength, and logical coherence. You do not favor seniority or prestige."
            )
            prompt = f"""
Debate Round {round_num} / {max_rounds}
Topic: {topic}

Content under debate:
{current_content[:4000]}

Dissenting arguments:
{chr(10).join(dissent_args)}

You must produce a resolution in JSON:
{{
  "resolution_text": "<summary of the decided position and reasoning>",
  "changes_required": ["specific change 1", "specific change 2"],
  "consensus_achieved": true/false,
  "winning_experts": ["names of experts whose position was adopted"],
  "losing_experts": ["names of experts whose position was rejected or partially accepted"]
}}

If consensus is not achieved and this is the last round, make a binding decision based on strongest evidence.
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
                    "resolution_text": raw[:1000],
                    "changes_required": ["Manual review needed due to parse error."],
                    "consensus_achieved": round_num >= max_rounds,
                    "winning_experts": [],
                    "losing_experts": [d.expert_name for d in dissenters],
                }

            resolution = data.get("resolution_text", "")
            changes_required = data.get("changes_required", [])
            consensus = data.get("consensus_achieved", False)

            if state:
                state.add_log(self.name, f"Debate Round {round_num} Resolution", resolution[:200], f"Consensus: {consensus}")

            if consensus:
                if state:
                    state.add_log(self.name, "Debate Resolved", f"Consensus at round {round_num}")
                return {
                    "resolved": True,
                    "rounds": round_num,
                    "final_resolution": resolution,
                    "changes_required": changes_required,
                    "winning_experts": data.get("winning_experts", []),
                    "losing_experts": data.get("losing_experts", []),
                }

            # Update content for next round if changes required
            if changes_required:
                current_content = self._apply_changes(current_content, changes_required)

        if state:
            state.add_log(self.name, "Binding Decision", f"Max rounds reached. Binding decision made.")
        return {
            "resolved": True,
            "rounds": round_num,
            "final_resolution": resolution,
            "changes_required": changes_required,
            "winning_experts": data.get("winning_experts", []),
            "losing_experts": data.get("losing_experts", []),
        }

    def _apply_changes(self, content: str, changes: List[str]) -> str:
        """Summarize changes to content for next debate round."""
        system = "You are a concise academic editor. Apply requested changes to a text. Return only the updated text."
        prompt = f"""
Apply the following changes to the text. Return the updated text only.

Changes:
{chr(10).join(changes)}

Text:
{content[:6000]}
"""
        return self.llm.generate(prompt, system, max_tokens=3000)
