from typing import List
from research_engine.models import ResearchState, SimulationResult
from research_engine.llm_client import LocalLLMClient
from tools import CodeInterpreterTool


class MethodologistAgent:
    """Agent responsible for executing real scientific investigations under 'Prof' standards."""
    def __init__(self, llm_client: LocalLLMClient):
        self.llm = llm_client
        self.name = "Lead Methodologist & Investigation Engineer"

    def execute(self, state: ResearchState) -> ResearchState:
        state.add_log(self.name, "Experimentation & Simulation", "Evaluating hypothesis requirements and designing study methodology...", f"Topic: '{state.topic}'")
        
        if not state.research_questions:
            state.add_log(self.name, "Experimentation & Simulation", "No hypothesis found. Skipping methodology execution.", status="completed")
            return state

        rq = state.research_questions[0]
        method_type = rq.methodology_type.lower()
        state.add_log(self.name, "Experimentation & Simulation", f"Selected discipline methodology: {method_type.upper()}", f"Hypothesis: {rq.hypothesis[:80]}...")

        # Case 1: Computational Simulation (Computer Science, Math, Physics, Engineering)
        if method_type in ["computational_simulation", "hybrid"] and ("comput" in method_type or "simul" in method_type or state.allow_code_execution):
            state.add_log(self.name, "Experimentation & Simulation", "Generating executable Python computational simulation script...")
            prompt_code = f"""Act as "Prof"—a world-class applied mathematician and computational scientist.
CORE PRINCIPLES: Accuracy before style. Precision before completeness. Write bug-free, vectorized code.

TASK:
Write a clean, standalone Python script using numpy, pandas, and matplotlib to empirically simulate and test the following scientific hypothesis for "{state.topic}":
Hypothesis: {rq.hypothesis}
Proposed Investigation: {rq.proposed_investigation}

Requirements:
1. Use numpy to generate synthetic baseline and proposed algorithm data across increasing dimensions or timesteps.
2. Calculate clear performance metrics (e.g. latency, error MSE, throughput, or accuracy).
3. Print a tabular summary table to stdout using pandas DataFrame.to_string().
4. Generate a clean comparative matplotlib chart and save it explicitly to "simulation_chart.png".
5. Do not include any interactive plt.show() calls, only plt.savefig('simulation_chart.png').
Output ONLY the executable Python code inside ```python ... ``` block."""

            raw_code = self.llm.generate(prompt=prompt_code, system_prompt="Act as Prof. Write bug-free, vectorized Python code.", max_tokens=2200)
            sim_result = CodeInterpreterTool.execute_code(raw_code, experiment_name=rq.question_id)
            
            state.simulation_results.append(sim_result)
            if sim_result.success:
                state.add_log(self.name, "Experimentation & Simulation", "Computational simulation completed successfully! Chart saved.", f"Findings: {sim_result.summary_findings}")
            else:
                state.add_log(self.name, "Experimentation & Simulation", "Simulation encountered an execution error.", f"Error: {sim_result.stderr}", status="error")

        # Case 2: Qualitative / Systematic Review / Non-Computational Investigations
        else:
            state.add_log(self.name, "Experimentation & Simulation", f"Executing {method_type.upper().replace('_', ' ')} protocol across scraped literature...", "Synthesizing evidence table...")
            
            papers_context = "\n".join([f"- {p.authors[0] if p.authors else 'Anon'} ({p.published_date[:4]}): '{p.title}' ({p.source})" for p in state.extracted_papers[:15]])
            
            pool_text = ""
            if state.uploaded_files_content:
                pool_text = f"\nNote: Incorporate analysis of user's uploaded documents under action: '{state.pool_action}'.\n"
            
            prompt_invest = f"""Act as "Prof"—a world-class research methodologist and journal editor.
CORE PRINCIPLES: Accuracy before style. Evidence before opinion. Never use unnecessary words. Never invent facts.

TASK:
Execute a formal methodological investigation for "{state.topic}" using a "{method_type.replace('_', ' ')}" approach tailored for deliverable type: "{state.target_deliverable}".
Evaluate the scraped academic works below against the research hypothesis: "{rq.hypothesis}".{pool_text}

Scraped Academic Works:
{papers_context}

Write a concise, professional Methodological Investigation Report containing:
1. Evidence Extraction Matrix (Compare findings, sample characteristics, and methodologies across the scraped papers).
2. Methodological Rigor & Validity Analysis.
3. Summary Findings confirming or modifying the hypothesis based strictly on the retrieved literature."""

            report_text = self.llm.generate(prompt=prompt_invest, system_prompt="Act as Prof. Rigorous methodological synthesis.", max_tokens=2200)
            
            sim_result = SimulationResult(
                experiment_name=rq.question_id,
                code_executed=None,
                stdout=report_text,
                success=True,
                summary_findings=f"{method_type.upper().replace('_', ' ')} investigation completed. Evidence table synthesized across {len(state.extracted_papers)} scraped works.",
                chart_path=None
            )
            state.simulation_results.append(sim_result)
            state.add_log(self.name, "Experimentation & Simulation", f"{method_type.replace('_', ' ').title()} investigation completed successfully!", status="completed")

        state.progress_percentage = 75
        return state
