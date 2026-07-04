import os
import subprocess
import tempfile
import time
from typing import Optional
from research_engine.models import SimulationResult


class CodeInterpreterTool:
    """Safely executes real Python scripts for computational data modeling and statistical evaluation."""
    
    @staticmethod
    def execute_code(code: str, experiment_name: str = "Simulation Experiment") -> SimulationResult:
        """
        Executes genuine Python code locally.
        Zero fake or hardcoded fallbacks.
        """
        clean_code = code.strip()
        if not clean_code:
            return SimulationResult(
                experiment_name=experiment_name,
                code_executed=None,
                stdout="No executable computational code was required or provided for this study methodology.",
                success=True,
                summary_findings="Investigation conducted via non-computational methodology (Qualitative Case Study / Meta-Analysis).",
                chart_path=None
            )

        if clean_code.startswith("```python"):
            clean_code = clean_code[len("```python"):].strip()
        elif clean_code.startswith("```"):
            clean_code = clean_code[len("```"):].strip()
        if clean_code.endswith("```"):
            clean_code = clean_code[:-len("```")].strip()

        chart_path = "simulation_chart.png"
        if os.path.exists(chart_path):
            try:
                os.remove(chart_path)
            except Exception:
                pass

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(clean_code)
                temp_file_path = temp_file.name

            start_time = time.time()
            result = subprocess.run(
                ["python3", temp_file_path],
                capture_output=True,
                text=True,
                timeout=45
            )
            duration = time.time() - start_time

            try:
                os.remove(temp_file_path)
            except Exception:
                pass

            success = (result.returncode == 0)
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            generated_chart = chart_path if os.path.exists(chart_path) else None

            summary = f"Execution completed in {duration:.2f}s. Status: {'SUCCESS' if success else 'FAILED'}."
            if success and stdout:
                summary += f"\nOutput Metrics:\n{stdout[:600]}..."

            return SimulationResult(
                experiment_name=experiment_name,
                code_executed=clean_code,
                stdout=stdout if stdout else "(No stdout produced)",
                stderr=stderr if stderr else None,
                success=success,
                summary_findings=summary,
                chart_path=generated_chart
            )

        except subprocess.TimeoutExpired:
            return SimulationResult(
                experiment_name=experiment_name,
                code_executed=clean_code,
                stdout="",
                stderr="Execution timed out after 45 seconds.",
                success=False,
                summary_findings="Computational simulation failed due to execution timeout.",
                chart_path=None
            )
        except Exception as e:
            return SimulationResult(
                experiment_name=experiment_name,
                code_executed=clean_code,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                success=False,
                summary_findings="Computational simulation failed during script execution.",
                chart_path=None
            )
