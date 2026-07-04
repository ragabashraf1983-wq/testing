import time
from typing import Optional, Callable, List, Dict
from research_engine.models import ResearchState
from research_engine.llm_client import LocalLLMClient
from research_engine.agents import LiteratureScoutAgent, GapAnalystAgent, MethodologistAgent, AcademicAuthorAgent
from research_engine.domain_engine import DomainIntelligenceEngine


class ResearchOrchestrator:
    """
    Core engine managing the autonomous multi-agent research workflow under 'Prof' academic standards.
    100% Real Scraping • Real LLM Reasoning • Target Deliverable Customization • Research Pool File Uploads.
    """
    def __init__(self, model_name: str = "ollama/llama3", base_url: str = "http://localhost:11434", temperature: float = 0.2):
        self.llm_client = LocalLLMClient(model_name=model_name, base_url=base_url, temperature=temperature)
        self.scout = LiteratureScoutAgent(self.llm_client)
        self.analyst = GapAnalystAgent(self.llm_client)
        self.methodologist = MethodologistAgent(self.llm_client)
        self.author = AcademicAuthorAgent(self.llm_client)

    def run_stage_1_literature(
        self,
        topic: str,
        target_deliverable: str = "Full Academic Research Paper (~4,000 - 8,000 words / 15-25 pages)",
        pool_action: str = "Think WITH the Draft (Expand & Corroborate)",
        uploaded_files: Optional[List[Dict[str, str]]] = None,
        allow_code_execution: bool = True,
        progress_callback: Optional[Callable[[ResearchState], None]] = None
    ) -> ResearchState:
        """Executes Stage 1: Live 4-database literature retrieval and analyzing uploaded pool documents."""
        state = ResearchState(
            topic=topic,
            target_deliverable=target_deliverable,
            pool_action=pool_action,
            uploaded_files_content=uploaded_files or [],
            llm_model=self.llm_client.model_name,
            temperature=self.llm_client.temperature,
            allow_code_execution=allow_code_execution
        )
        
        state.add_log("System Orchestrator", "Initialized", f"Starting deep real investigation on: '{topic}'", f"Deliverable: {target_deliverable}")
        if uploaded_files:
            state.add_log("System Orchestrator", "Research Pool Loaded", f"Loaded {len(uploaded_files)} uploaded document(s) into Research Pool.", f"Action: {pool_action}")
            
        if progress_callback:
            progress_callback(state)
        time.sleep(0.2)

        # Execute Literature Scout
        state = self.scout.execute(state)
        
        # Pre-generate methodology classification for consultation
        disc, rec_method, _ = DomainIntelligenceEngine.classify_domain_and_methodology(state.topic)
        if not state.research_questions:
            from research_engine.models import ResearchQuestion
            state.research_questions = [
                ResearchQuestion(
                    question_id="RQ-01",
                    question=f"How can structured intervention frameworks resolve operational limitations in {state.topic}?",
                    hypothesis=f"Adopting a systematic {rec_method.replace('_', ' ')} protocol will improve empirical reliability and reduce operational error variance.",
                    methodology_type=rec_method,
                    proposed_investigation=f"Execute a rigorous {rec_method.replace('_', ' ')} across scraped works and institutional benchmarks."
                )
            ]
        
        state.current_stage = "Consultation"
        state.add_log("System Orchestrator", "Consultation Required", "Pausing workflow for user strategy confirmation...", status="completed")
        if progress_callback:
            progress_callback(state)
            
        return state

    def run_stages_2_to_4(
        self,
        state: ResearchState,
        confirmed_gap_index: int = 0,
        confirmed_methodology: Optional[str] = None,
        user_emphasis: Optional[str] = None,
        progress_callback: Optional[Callable[[ResearchState], None]] = None
    ) -> ResearchState:
        """Resumes workflow from consultation: executes Stage 2 (Gaps), Stage 3 (Methodology), and Stage 4 (Author)."""
        state.add_log("System Orchestrator", "Strategy Confirmed", "User confirmed research direction. Resuming deep analytical workflow...")
        if progress_callback:
            progress_callback(state)
        time.sleep(0.2)

        if state.identified_gaps and 0 <= confirmed_gap_index < len(state.identified_gaps):
            selected_gap = state.identified_gaps[confirmed_gap_index]
            state.identified_gaps = [selected_gap] + [g for i, g in enumerate(state.identified_gaps) if i != confirmed_gap_index]
            state.add_log("System Orchestrator", "Strategy Confirmed", f"Locked target research gap: [{selected_gap.gap_id}] {selected_gap.title}")

        if confirmed_methodology and state.research_questions:
            state.research_questions[0].methodology_type = confirmed_methodology.lower().replace(" ", "_")
            state.add_log("System Orchestrator", "Strategy Confirmed", f"Locked investigation methodology: {confirmed_methodology.upper()}")

        if user_emphasis and state.research_questions:
            state.research_questions[0].proposed_investigation += f" (User Focus Emphasis: {user_emphasis})"
            state.add_log("System Orchestrator", "Strategy Confirmed", f"Added custom research emphasis: '{user_emphasis}'")

        # Execute Stage 2: Gap Analyst
        state = self.analyst.execute(state)
        if progress_callback:
            progress_callback(state)
        time.sleep(0.2)

        # Execute Stage 3: Lead Methodologist
        state = self.methodologist.execute(state)
        if progress_callback:
            progress_callback(state)
        time.sleep(0.2)

        # Execute Stage 4: Academic Author
        state = self.author.execute(state)
        if progress_callback:
            progress_callback(state)

        state.current_stage = "Completed"
        state.add_log("System Orchestrator", "Completed", f"Full citation-backed deliverable generated successfully!", status="completed")
        if progress_callback:
            progress_callback(state)

        return state

    def run_pipeline(
        self,
        topic: str,
        target_deliverable: str = "Full Academic Research Paper (~4,000 - 8,000 words / 15-25 pages)",
        pool_action: str = "Think WITH the Draft (Expand & Corroborate)",
        uploaded_files: Optional[List[Dict[str, str]]] = None,
        allow_code_execution: bool = True,
        progress_callback: Optional[Callable[[ResearchState], None]] = None
    ) -> ResearchState:
        """Backward-compatible single-pass execution."""
        state = self.run_stage_1_literature(topic, target_deliverable, pool_action, uploaded_files, allow_code_execution, progress_callback)
        return self.run_stages_2_to_4(state, progress_callback=progress_callback)
