"""
v5 Experiment Design Agent — Detects when empirical validation is needed, designs experiments,
and notifies the user to perform them in a lab or real-world setting.
"""

import json
import os
import time
from typing import Dict, Any, List, Optional

from research_engine.models import ResearchState
from research_engine.llm_client import LocalLLMClient


class ExperimentAgent:
    """Designs experiments and notifies user for real-world execution."""

    def __init__(self, llm_client: LocalLLMClient, notification_path: str = "./experiments/pending_experiments.json"):
        self.name = "ExperimentAgent"
        self.llm = llm_client
        self.notification_path = notification_path
        os.makedirs(os.path.dirname(notification_path) if os.path.dirname(notification_path) else ".", exist_ok=True)

    def assess_need(self, topic: str, outline: List[str], state: ResearchState = None) -> bool:
        """Determine if the research requires empirical experiments."""
        system = "You are a research methodology advisor. Determine if empirical validation is needed."
        prompt = f"""
Topic: {topic}
Outline: {outline}

Does this research require real experiments (lab, field, simulation, survey)?
Answer ONLY with JSON: {{"required": true/false, "reason": "...", "scope": "lab|field|simulation|survey|meta_analysis"}}
"""
        raw = self.llm.generate(prompt, system, max_tokens=800)
        try:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                data = json.loads(raw[start:end+1])
            else:
                data = json.loads(raw.strip().strip("`").replace("json", "").strip())
            needed = data.get("required", False)
        except Exception:
            needed = False
            data = {"required": False, "reason": "parse error", "scope": "unknown"}

        if state:
            state.add_log(self.name, "Assess Experiment Need", data.get("reason", ""), f"Required: {needed}")
        return needed

    def design_experiment(self, topic: str, outline: List[str],
                          existing_sections: Dict[str, str], state: ResearchState = None) -> Dict[str, Any]:
        system = "You are an experimental design expert. Create rigorous, reproducible protocols."
        prompt = f"""
Design an experiment for the research on "{topic}".

Current outline: {outline}

Draft context (if available):
{json.dumps({k: v[:1500] for k, v in existing_sections.items()}, indent=2)}

Provide a detailed experiment design in JSON:
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
  "scope": "lab|field|simulation|survey"
}}
"""
        raw = self.llm.generate(prompt, system, max_tokens=2200)
        try:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                design = json.loads(raw[start:end+1])
            else:
                design = json.loads(raw.strip().strip("`").replace("json", "").strip())
        except Exception:
            design = {
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
        design["experiment_id"] = exp_id
        design["status"] = "PENDING_USER"
        design["created_at"] = time.time()

        if state:
            state.experiments.append(design)
            state.add_log(self.name, "Design Experiment", design["title"], f"ID: {exp_id}")
        return design

    def notify_user(self, design: Dict[str, Any], state: ResearchState = None):
        """Write notification to file so user sees it."""
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
        """When user returns results, integrate them into the paper."""
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

Generate:
1. A polished Results section paragraph(s) describing the findings.
2. A Discussion section paragraph(s) interpreting the results, comparing with hypothesis, and noting limitations.

Output in Markdown.
"""
        integrated = self.llm.generate(prompt, system, max_tokens=3000)
        if state:
            state.add_log(self.name, "Integrate Experiment Results", f"Integrated results for {experiment_id}")
        return integrated
