import time
import os
from typing import Optional, Callable, List, Dict, Any

from research_engine.models import ResearchState
from research_engine.llm_client import LocalLLMClient
from research_engine.agents import LiteratureScoutAgent, GapAnalystAgent, MethodologistAgent, AcademicAuthorAgent
from research_engine.agents.domain_expert_council import DomainExpertCouncil
from research_engine.agents.peer_review_board import PeerReviewBoard
from research_engine.agents.conflict_resolution import ConflictResolutionAgent
from research_engine.agents.experiment_agent import ExperimentAgent
from research_engine.domain_engine import DomainIntelligenceEngine
from research_engine.graph_tracker import GraphTracker
from research_engine.audit_logger import AuditLogger
from research_engine.project_history import ProjectHistory


class ResearchOrchestrator:
    """
    Core engine managing the autonomous multi-agent research workflow.
    v5: Robust LLM failure detection, early abort, and quality validation.
    """
    def __init__(self, model_name: str = "ollama/llama3", base_url: str = "http://localhost:11434", temperature: float = 0.2, api_key: Optional[str] = None):
        self.llm_client = LocalLLMClient(model_name=model_name, base_url=base_url, temperature=temperature, api_key=api_key)

        self.scout = LiteratureScoutAgent(self.llm_client)
        self.analyst = GapAnalystAgent(self.llm_client)
        self.methodologist = MethodologistAgent(self.llm_client)
        self.author = AcademicAuthorAgent(self.llm_client)

        self.expert_council = DomainExpertCouncil(self.llm_client)
        self.peer_review_board = PeerReviewBoard(self.llm_client)
        self.conflict_resolver = ConflictResolutionAgent(self.llm_client)
        self.experiment_agent = ExperimentAgent(self.llm_client)

        self.tracker = GraphTracker("orchestrator")
        self.audit = AuditLogger()
        self.history = ProjectHistory()

    def run_v5_pipeline(
        self,
        topic: str,
        target_deliverable: str = "Full Academic Research Paper (~4,000 - 8,000 words / 15-25 pages)",
        pool_action: str = "Think WITH the Draft (Expand & Corroborate)",
        uploaded_files: Optional[List[Dict[str, str]]] = None,
        allow_code_execution: bool = True,
        progress_callback: Optional[Callable[[ResearchState], None]] = None
    ) -> ResearchState:
        """v5: Full pipeline with robust LLM failure detection and early abort."""
        state = ResearchState(
            topic=topic,
            target_deliverable=target_deliverable,
            pool_action=pool_action,
            uploaded_files_content=uploaded_files or [],
            llm_model=self.llm_client.model_name,
            temperature=self.llm_client.temperature,
            allow_code_execution=allow_code_execution
        )

        state.add_log("System Orchestrator", "Initialized", f"Starting v5 deep investigation on: '{topic}'", f"Deliverable: {target_deliverable}")
        self._save_state(state)
        if progress_callback:
            progress_callback(state)
        time.sleep(0.2)

        # Stage 1: Literature Scout
        self._run_literature(state, progress_callback)
        self._save_state(state)

        # Check LLM quality after literature stage
        if self._llm_quality_too_low(state):
            state.add_log("System Orchestrator", "LLM QUALITY WARNING", "LLM producing weak/empty responses. Recommend switching to a stronger model (GPT-4o, Claude-3.5, llama3.1:70b, or similar).", status="warning")
            state.status = "llm_quality_warning"
            self._save_state(state)
            return state

        # Stage 2: Gap Analysis
        self._run_gap_analysis(state, progress_callback)
        self._save_state(state)

        # Stage 3: Methodology
        self._run_methodology(state, progress_callback)
        self._save_state(state)

        # Stage 4: Expert Council Evaluation
        expert_result = self._run_expert_council(state, progress_callback)
        self._save_state(state)

        if expert_result.get("llm_failure_detected"):
            state.add_log("System Orchestrator", "Expert Council Warning", "All experts returned identical fallback scores. LLM is too weak for structured evaluation. Continuing with degraded quality.", status="warning")

        # Stage 5: Chunked Drafting
        self._run_chunked_drafting(state, progress_callback)
        self._save_state(state)

        # Check if sections are actually populated
        if not state.sections or all(len(s) < 200 for s in state.sections.values()):
            state.add_log("System Orchestrator", "DRAFTING FAILED", "All sections are empty or too short. LLM is not producing content. Aborting peer review.", status="error")
            state.status = "drafting_failed"
            self._run_final_export(state, progress_callback)
            self._save_state(state)
            return state

        # Stage 6: Peer Review Board
        review_result = self._run_peer_review(state, progress_callback)
        self._save_state(state)

        if review_result and review_result.get("llm_failure_detected"):
            state.add_log("System Orchestrator", "Peer Review Warning", "All reviewers returned identical fallback scores. LLM cannot perform structured peer review. Skipping revision loops.", status="warning")
            # Don't loop infinitely with fake scores
            state.draft_iteration = state.max_draft_iterations

        # Stage 7: Experiment Assessment
        self._run_experiment_assessment(state, progress_callback)
        self._save_state(state)

        # Stage 8: Final Edit & Export
        self._run_final_export(state, progress_callback)
        self._save_state(state)

        state.current_stage = "Completed"
        state.status = "complete"
        state.add_log("System Orchestrator", "Completed", "v5 Full pipeline completed successfully!", status="completed")
        self._save_state(state)
        if progress_callback:
            progress_callback(state)
        return state

    def _llm_quality_too_low(self, state: ResearchState) -> bool:
        """Detect if the LLM is producing garbage/empty responses."""
        if self.llm_client.quality_score < 0.3:
            return True
        # Check if literature summary is empty or too short
        if not state.literature_summary or len(state.literature_summary) < 200:
            return True
        return False

    def _run_literature(self, state: ResearchState, progress_callback: Optional[Callable] = None):
        state.add_log("System Orchestrator", "Stage 1", "Literature Retrieval across 4 databases...")
        state = self.scout.execute(state)
        if progress_callback:
            progress_callback(state)
        time.sleep(0.2)

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

    def _run_gap_analysis(self, state: ResearchState, progress_callback: Optional[Callable] = None):
        state.add_log("System Orchestrator", "Stage 2", "Gap Analysis & Hypothesis Formation...")
        state = self.analyst.execute(state)
        if progress_callback:
            progress_callback(state)
        time.sleep(0.2)

    def _run_methodology(self, state: ResearchState, progress_callback: Optional[Callable] = None):
        state.add_log("System Orchestrator", "Stage 3", "Methodology & Investigation Execution...")
        state = self.methodologist.execute(state)
        if progress_callback:
            progress_callback(state)
        time.sleep(0.2)

    def _run_expert_council(self, state: ResearchState, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        state.add_log("System Orchestrator", "Stage 4", "Expert Council Evaluation (7 specialists)...")

        content = f"""
Topic: {state.topic}
Literature Summary: {state.literature_summary[:2000]}
Target Gap: {state.identified_gaps[0].title if state.identified_gaps else 'None'}
Hypothesis: {state.research_questions[0].hypothesis if state.research_questions else 'None'}
Methodology: {state.research_questions[0].methodology_type if state.research_questions else 'None'}
"""
        eval_result = self.expert_council.evaluate(content, context="Pre-draft research direction", state=state)

        from research_engine.models import ExpertReviewEntry
        for r in eval_result["reviews"]:
            state.expert_reviews.append(ExpertReviewEntry(
                expert_name=r.expert_name,
                domain=r.domain,
                score=r.score,
                confidence=r.confidence,
                criticisms=r.criticisms,
                suggestions=r.suggestions,
                endorsements=r.endorsements,
                dissent=r.dissent,
                dissent_reason=r.dissent_reason,
            ))

        if progress_callback:
            progress_callback(state)
        time.sleep(0.2)

        if eval_result["consensus_level"] < state.expert_consensus_threshold and not eval_result.get("llm_failure_detected"):
            state.add_log("System Orchestrator", "Stage 4b", "Expert consensus low — initiating structured debate...")
            debate = self.conflict_resolver.debate(
                content=content,
                expert_reviews=eval_result["reviews"],
                topic="Research Direction",
                max_rounds=state.max_expert_debate_rounds,
                consensus_threshold=state.expert_consensus_threshold,
                state=state,
            )
            from research_engine.models import ConflictEntry
            state.conflicts.append(ConflictEntry(
                round=debate.get("rounds", 0),
                topic="Research Direction",
                dissenters=debate.get("losing_experts", []),
                resolution=debate.get("final_resolution", ""),
                changes_required=debate.get("changes_required", []),
                winning_experts=debate.get("winning_experts", []),
                losing_experts=debate.get("losing_experts", []),
            ))
            state.resolutions.append(debate.get("final_resolution", ""))
            if progress_callback:
                progress_callback(state)

        return eval_result

    def _run_chunked_drafting(self, state: ResearchState, progress_callback: Optional[Callable] = None):
        state.add_log("System Orchestrator", "Stage 5", "Chunked Section Drafting (prevents context collapse)...")
        state = self.author.execute(state)
        if progress_callback:
            progress_callback(state)
        time.sleep(0.2)

    def _run_peer_review(self, state: ResearchState, progress_callback: Optional[Callable] = None) -> Optional[Dict[str, Any]]:
        state.add_log("System Orchestrator", "Stage 6", "Peer Review Board (Editor + 5 reviewers)...")

        paper_text = state.final_manuscript_md
        last_review = None

        for round_num in range(1, state.max_peer_review_rounds + 1):
            state.peer_review_round = round_num
            state.add_log("System Orchestrator", f"Peer Review Round {round_num}", f"Submitting to review board...")

            review_result = self.peer_review_board.review(paper_text, round_num, state)
            last_review = review_result

            from research_engine.models import PeerReviewEntry
            for d in review_result["reviewer_decisions"]:
                state.peer_reviews.append(PeerReviewEntry(
                    round=round_num,
                    reviewer=d.reviewer,
                    verdict=d.verdict,
                    score=d.score,
                    comments=d.comments,
                    specific_issues=d.specific_issues,
                ))

            if progress_callback:
                progress_callback(state)

            # If LLM failure detected, don't waste time on fake loops
            if review_result.get("llm_failure_detected"):
                state.add_log("System Orchestrator", "Peer Review Abort", "LLM producing identical fallback scores. Skipping revision loops.", status="warning")
                break

            if review_result["final_verdict"] in ("ACCEPT", "MINOR_REVISION"):
                state.add_log("System Orchestrator", f"Peer Review Round {round_num}", f"Verdict: {review_result['final_verdict']}")
                break

            state.add_log("System Orchestrator", f"Revision Round {round_num}", f"Verdict: {review_result['final_verdict']} — revising...")
            state.draft_iteration += 1
            if state.draft_iteration > state.max_draft_iterations:
                state.add_log("System Orchestrator", "Max Revisions", "Max draft iterations reached. Proceeding with current version.", status="warning")
                break

            paper_text = self.author.revise_for_peer_review(state)
            state.final_manuscript_md = paper_text
            if progress_callback:
                progress_callback(state)
            time.sleep(0.2)

        return last_review

    def _run_experiment_assessment(self, state: ResearchState, progress_callback: Optional[Callable] = None):
        state.add_log("System Orchestrator", "Stage 7", "Experiment Assessment...")
        needs_exp = self.experiment_agent.assess_need(state.topic, state.outline, state)
        if needs_exp:
            design = self.experiment_agent.design_experiment(
                state.topic, state.outline, state.sections, state
            )
            self.experiment_agent.notify_user(design, state)
            state.status = "paused_for_experiment"
            state.add_log("System Orchestrator", "Experiment Required", f"User must perform experiment: {design['experiment_id']}", status="waiting")
            if progress_callback:
                progress_callback(state)
        else:
            state.add_log("System Orchestrator", "Experiment Assessment", "No empirical experiments required for this topic.")

    def _run_final_export(self, state: ResearchState, progress_callback: Optional[Callable] = None):
        state.add_log("System Orchestrator", "Stage 8", "Final Edit, Audit Export, and Graph Generation...")

        # Final edit (copy editing)
        system = "You are a senior copy editor for a Q1 journal. Fix grammar, improve flow, ensure consistent terminology, and format citations properly."
        prompt = f"Edit and polish the following paper for final submission:\n\n{state.final_manuscript_md[:12000]}"
        edited = self.llm_client.generate(prompt, system, max_tokens=4000)
        if edited and not edited.startswith("[LLM"):
            state.final_manuscript_md = edited

        # Save paper
        paper_path = self.author.save_paper(state)

        # Export graph
        graph_path = f"./sample_outputs/{state.project_id}_graph.html"
        self.tracker.export_html(graph_path)
        state.graph_path = graph_path

        # Export audit log
        audit_path = self.audit.export_full_md(
            state.project_id,
            self._build_audit_memory(state)
        )
        state.audit_log_path = audit_path

        state.add_log("System Orchestrator", "Final Export", f"Paper: {paper_path}, Graph: {graph_path}, Audit: {audit_path}")
        if progress_callback:
            progress_callback(state)

    def _save_state(self, state: ResearchState):
        self.history.save_project(
            project_id=state.project_id,
            title=state.topic,
            topic=state.topic,
            status=state.status,
            current_state=state.current_stage,
            draft_iteration=state.draft_iteration,
            peer_review_round=state.peer_review_round,
            snapshot=state.to_snapshot(),
        )
        for log in state.logs:
            self.audit.log(
                project_id=state.project_id,
                agent=log.agent_name,
                role="Agent",
                action=log.action,
                state=state.current_stage,
                content=log.details or "",
                metadata={"stage": log.stage, "status": log.status},
                severity="INFO" if log.status != "error" else "ERROR",
            )

    def _build_audit_memory(self, state: ResearchState) -> str:
        parts = [
            f"Project: {state.topic}",
            f"ID: {state.project_id}",
            f"Status: {state.status}",
            f"Stage: {state.current_stage}",
            f"Draft Iteration: {state.draft_iteration}",
            f"Peer Review Round: {state.peer_review_round}",
            f"LLM Quality Score: {self.llm_client.quality_score:.2f}",
            "\n=== OUTLINE ===\n",
            "\n".join(f"{i+1}. {s}" for i, s in enumerate(state.outline)),
            "\n=== EXPERT REVIEWS ===\n",
        ]
        for e in state.expert_reviews:
            parts.append(f"- {e.expert_name}: score={e.score}, dissent={e.dissent}")
        parts.append("\n=== PEER REVIEWS ===\n")
        for p in state.peer_reviews:
            parts.append(f"- Round {p.round} {p.reviewer}: {p.verdict} ({p.score})")
        parts.append("\n=== CONFLICTS ===\n")
        for c in state.conflicts:
            parts.append(f"- Round {c.round}: {c.topic} -> {c.resolution}")
        parts.append("\n=== EXPERIMENTS ===\n")
        for exp in state.experiments:
            parts.append(f"- {exp.get('experiment_id', 'N/A')}: {exp.get('title', 'N/A')} [{exp.get('status', 'N/A')}]")
        return "\n".join(parts)

    # --- v4 Backward Compatible Methods ---

    def run_stage_1_literature(
        self,
        topic: str,
        target_deliverable: str = "Full Academic Research Paper (~4,000 - 8,000 words / 15-25 pages)",
        pool_action: str = "Think WITH the Draft (Expand & Corroborate)",
        uploaded_files: Optional[List[Dict[str, str]]] = None,
        allow_code_execution: bool = True,
        progress_callback: Optional[Callable[[ResearchState], None]] = None
    ) -> ResearchState:
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

        state = self.scout.execute(state)

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

        state = self.analyst.execute(state)
        if progress_callback:
            progress_callback(state)
        time.sleep(0.2)

        state = self.methodologist.execute(state)
        if progress_callback:
            progress_callback(state)
        time.sleep(0.2)

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
