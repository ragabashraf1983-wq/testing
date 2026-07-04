import time
import uuid
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


class ExpertReviewEntry(BaseModel):
    """v5: Record of a domain expert evaluation."""
    expert_name: str
    domain: str
    score: float
    confidence: float
    criticisms: List[str] = []
    suggestions: List[str] = []
    endorsements: List[str] = []
    dissent: bool = False
    dissent_reason: str = ""


class PeerReviewEntry(BaseModel):
    """v5: Record of a peer review round."""
    round: int
    reviewer: str
    verdict: str
    score: float
    comments: str
    specific_issues: List[str] = []


class ConflictEntry(BaseModel):
    """v5: Record of a conflict debate."""
    round: int
    topic: str
    dissenters: List[str]
    resolution: str
    changes_required: List[str] = []
    winning_experts: List[str] = []
    losing_experts: List[str] = []


class ExperimentEntry(BaseModel):
    """v5: Record of an experiment design."""
    experiment_id: str
    title: str
    objective: str
    hypothesis: str
    variables: Dict[str, Any] = {}
    materials: List[str] = []
    procedure: List[str] = []
    expected_results: str = ""
    data_collection: str = ""
    analysis_plan: str = ""
    safety_notes: str = ""
    duration_estimate: str = ""
    scope: str = ""
    status: str = "PENDING_USER"
    created_at: float = 0.0
    user_results: str = ""
    user_analysis: str = ""
    completed_at: Optional[float] = None


class ResearchState(BaseModel):
    """The central state object shared across the multi-agent workflow. v5 extended."""
    # Identity
    project_id: str = Field(default_factory=lambda: f"proj_{uuid.uuid4().hex[:8]}_{int(time.time())}")
    topic: str
    target_deliverable: str = "Full Academic Research Paper (~4,000 - 8,000 words / 15-25 pages)"
    pool_action: str = "Think WITH the Draft (Expand & Corroborate)"
    uploaded_files_content: List[Dict[str, str]] = []

    # Workflow state
    current_stage: str = "Initialized"
    status: str = "in_progress"
    progress_percentage: int = 0
    start_time: float = Field(default_factory=time.time)

    # Collected Artifacts
    extracted_papers: List[PaperMetadata] = []
    literature_summary: str = ""
    identified_gaps: List[ResearchGap] = []
    research_questions: List[ResearchQuestion] = []
    simulation_results: List[SimulationResult] = []
    final_manuscript_md: str = ""

    # v5: Chunked drafting
    outline: List[str] = []
    sections: Dict[str, str] = {}
    draft_iteration: int = 0

    # v5: Expert Council & Peer Review
    expert_reviews: List[ExpertReviewEntry] = []
    peer_review_round: int = 0
    peer_reviews: List[PeerReviewEntry] = []
    conflicts: List[ConflictEntry] = []
    resolutions: List[str] = []

    # v5: Experiments
    experiments: List[ExperimentEntry] = []
    experiment_notification_path: str = "./experiments/pending_experiments.json"

    # v5: Audit & Graph
    audit_log_path: str = ""
    graph_path: str = ""

    # Execution Logs
    logs: List[AgentLog] = []

    # Configuration
    llm_model: str = "ollama/llama3"
    temperature: float = 0.2
    allow_code_execution: bool = True

    # v5: Controls
    max_draft_iterations: int = 5
    max_peer_review_rounds: int = 3
    max_expert_debate_rounds: int = 3
    peer_review_accept_threshold: float = 0.75
    expert_consensus_threshold: float = 0.60

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

    def to_snapshot(self) -> Dict[str, Any]:
        """v5: Export full state as a JSON-serializable dict for persistence."""
        return self.model_dump()
