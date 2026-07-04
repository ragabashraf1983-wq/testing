import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PaperMetadata(BaseModel):
    """Metadata representing a verified academic publication."""
    title: str
    authors: List[str]
    published_date: str
    abstract: str
    url: str
    source: str
    citation_count: Optional[int] = 0
    key_findings: Optional[str] = ""
    methodology_summary: Optional[str] = ""


class ResearchGap(BaseModel):
    """Represents an identified contradiction, limitation, or gap in the literature."""
    gap_id: str
    title: str
    description: str
    significance: str
    related_papers: List[str]


class ResearchQuestion(BaseModel):
    """Formulated research question and scientific hypothesis."""
    question_id: str
    question: str
    hypothesis: str
    methodology_type: str
    proposed_investigation: str


class SimulationResult(BaseModel):
    """Result from automated code execution or analytical investigation."""
    experiment_name: str
    code_executed: Optional[str] = None
    stdout: str
    stderr: Optional[str] = None
    success: bool
    summary_findings: str
    chart_path: Optional[str] = None


class AgentLog(BaseModel):
    """Represents a live audit log entry from an agent during workflow execution."""
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    agent_name: str
    stage: str
    action: str
    details: Optional[str] = None
    status: str = "running"


class ResearchState(BaseModel):
    """The central state object shared across the multi-agent workflow."""
    topic: str
    target_deliverable: str = "Full Academic Research Paper (~4,000 - 8,000 words / 15-25 pages)"
    pool_action: str = "Think WITH the Draft (Expand & Corroborate)"
    uploaded_files_content: List[Dict[str, str]] = []
    
    current_stage: str = "Initialized"
    progress_percentage: int = 0
    start_time: float = Field(default_factory=time.time)
    
    # Collected Artifacts
    extracted_papers: List[PaperMetadata] = []
    literature_summary: str = ""
    identified_gaps: List[ResearchGap] = []
    research_questions: List[ResearchQuestion] = []
    simulation_results: List[SimulationResult] = []
    final_manuscript_md: str = ""
    
    # Execution Logs
    logs: List[AgentLog] = []
    
    # Configuration
    llm_model: str = "ollama/llama3"
    temperature: float = 0.2
    allow_code_execution: bool = True

    def add_log(self, agent: str, stage: str, action: str, details: Optional[str] = None, status: str = "completed"):
        """Helper to append a log entry and update current stage."""
        log_entry = AgentLog(
            agent_name=agent,
            stage=stage,
            action=action,
            details=details,
            status=status
        )
        self.logs.append(log_entry)
        self.current_stage = stage
