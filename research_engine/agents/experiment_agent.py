"""
v5 Experiment Design Agent — Robust JSON extraction with fallback.
"""

import os
import time
from typing import Dict, Any, List, Optional

from research_engine.models import ResearchState
from research_engine.llm_client import LocalLLMClient


class ExperimentAgent:
    def __init__(self, llm_client: LocalLLMClient, notification_path: str = "./experiments/pending_experiments.json"):
        self.name = "ExperimentAgent"
        self.llm = llm_client
        self.notification_path = notification_path
        os.makedirs(os.path.dirname(notification_path) if os.path.dirname(notification_path) else ".", exist_ok=True)

    def assess_need(self, topic: str, outline: List[str], state: ResearchState = None) -> bool:
        system = "You are a research methodology advisor. Determine if empirical validation is needed. Respond with JSON only."
        prompt = f"""
Topic: {topic}
Outline: {outline}

Does this research require real experiments (lab, field, simulation, survey)?
Respond ONLY with raw JSON (no markdown, no code blocks):
{{"required": true, "reason": "...", "scope": "lab"}}
"""
        raw = self.llm.generate(prompt, system, max_tokens=800)
        data = self.llm.extract_json(raw)
        if data is None:
            # Fallback: parse text
            needed = "yes" in raw.lower() or "true" in raw.lower()
            data = {"required": needed, "reason": raw[:500], "scope": "lab"}

        needed = data.get("required", False) if isinstance(data, dict) else False
        if state:
            state.add_log(self.name, "Assess Experiment Need", data.get("reason", ""), f"Required: {needed}")
        return needed

    def design_experiment(self, topic: str, outline: List[str],
                          existing_sections: Dict[str, str], state: ResearchState = None) -> Dict[str, Any]:
        system = "You are an experimental design expert. Create rigorous, reproducible protocols. Respond with JSON only."
        prompt = f"""
Design an experiment for the research on "{topic}".

Current outline: {outline}

Draft context (if available):
{existing_sections}

Provide a detailed experiment design in EXACT JSON format (no markdown, no code blocks, raw JSON only):
{{
  "title": "Experiment Title",
  "objective": "...",
  "hypothesis": "...",
  "variables": {{"independent": [...], "dependent": [...], "controlled": [...]}},
  "materials": [...],
  "procedure": ["step 1", "step 2", ...],
  "expected_results": "...",
  "data_collection": "...",
  "analysis_plan": "...",
  "safety_notes": "...",
  "duration_estimate": "...",
  "scope": "lab"
}}
"""
        raw = self.llm.generate(prompt, system, max_tokens=2200)
        data = self.llm.extract_json(raw)

        if data is None or data.get("_parse_error"):
            data = {
                "title": f"Experiment for {topic}",
                "objective": "Empirical validation",
                "hypothesis": "TBD",
                "variables": {},
                "materials": [],
                "procedure": ["Design experiment", "Collect data", "Analyze"],
                "expected_results": "TBD",
                "data_collection": "TBD",
                "analysis_plan": "TBD",
                "safety_notes": "Standard precautions",
                "duration_estimate": "Unknown",
                "scope": "lab",
            }

        exp_id = f"EXP_{state.project_id if state else 'unknown'}_{int(time.time())}"
        data["experiment_id"] = exp_id
        data["status"] = "PENDING_USER"
        data["created_at"] = time.time()

        if state:
            state.experiments.append(data)
            state.add_log(self.name, "Design Experiment", data["title"], f"ID: {exp_id}")
        return data

    def notify_user(self, design: Dict[str, Any], state: ResearchState = None):
        notifications = []
        if os.path.exists(self.notification_path):
            with open(self.notification_path, "r", encoding="utf-8") as f:
                try:
                    notifications = json.load(f)
                except Exception:
                    notifications = []

        notifications.append(design)
        with open(self.notification_path, "w", encoding="utf-8") as f:
            json.dump(notifications, f, indent=2)

        if state:
            state.add_log(self.name, "Notify User", f"Notification written to {self.notification_path}", f"Experiment: {design['experiment_id']}")

    def integrate_results(self, experiment_id: str, results: str, analysis: str = "",
                          state: ResearchState = None) -> str:
        exp = None
        if state:
            exp = next((e for e in state.experiments if e.get("experiment_id") == experiment_id), None)
        if not exp:
            if state:
                state.add_log(self.name, "Integrate Results Error", "Experiment ID not found.", status="error")
            return ""

        exp["status"] = "COMPLETED"
        exp["user_results"] = results
        exp["user_analysis"] = analysis
        exp["completed_at"] = time.time()

        system = "You are an academic author integrating experimental results into a paper."
        prompt = f"""
Integrate the following experimental results into the Results and Discussion sections.

Experiment: {exp['title']}
Hypothesis: {exp['hypothesis']}

Results provided by user:
{results}

User's preliminary analysis:
{analysis}

Generate polished Results and Discussion paragraphs in Markdown.
"""
        integrated = self.llm.generate(prompt, system, max_tokens=3000)
        if state:
            state.add_log(self.name, "Integrate Experiment Results", f"Integrated results for {experiment_id}")
        return integrated
