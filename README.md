# Autonomous Research Agent — v5 Upgrade

A multi-agent autonomous research system that produces publication-quality academic papers with adversarial expert debate, rigorous peer review, real-world experiment integration, and full audit trails.

## 🚀 What's New in v5

| Feature | v4 Limitation | v5 Solution |
|---------|---------------|-------------|
| **Long-form generation** | Local model collapsed on long papers; never produced final paper | **Chunked section drafting** — each section (Abstract, Intro, Literature Review, Methodology, Results, Discussion, Conclusion) is generated independently with memory context, so local LLMs never choke |
| **Expert depth** | Generic, agreeing agents | **Domain Expert Council** — 7 specialists (Linguist, Mathematician, Physicist, Statistician, Methodologist, Logistician, Epistemologist) with adversarial evaluation and explicit dissent tracking |
| **Real discussion** | Echo chamber; agents only agreed | **Conflict Resolution Agent** — forces structured debate rounds with winners/losers tracked and binding arbitration after max rounds |
| **Real experiments** | No lab validation | **Experiment Agent** — designs protocols, notifies the user to perform real lab/field/simulation work, and integrates results back into the paper |
| **Peer review** | No review gate | **Peer Review Board** — Chief Editor + 5 specialist reviewers (Methodology, Literature, Results, Impact, Novelty) with Q1/Q2 standards; accepts, rejects, or loops back for revision |
| **Process visibility** | Black box | **Real-time graph** — exports interactive D3.js force-directed graph showing every agent, state, and active node; open in any browser |
| **Project history** | Lost when closed | **SQLite persistence** — save/resume/continuation, versioning, and cross-project referencing |
| **Audit trail** | No logs | **Full Markdown audit log** — timestamped with every agent action, conflict, resolution, and severity level |

## 📁 Architecture

```
├── app.py                                    # Streamlit UI (Apple Dark Mode) — v5 tabs added
├── requirements.txt                          # Python dependencies (added networkx)
├── config/
│   ├── agents.yaml                           # Persona configs (v5 Expert Council + Peer Review Board)
│   └── tasks.yaml                            # Task definitions (v5 tasks added)
├── research_engine/
│   ├── __init__.py                           # Package exports (v5 models + modules)
│   ├── models.py                             # Pydantic models (v5: ExpertReviewEntry, PeerReviewEntry, ConflictEntry, ExperimentEntry)
│   ├── llm_client.py                         # Ollama / OpenAI-compatible client (v4 — unchanged)
│   ├── domain_engine.py                      # Topic classification (v4 — unchanged)
│   ├── orchestrator.py                       # Central state machine (v5: full pipeline + backward-compatible v4 methods)
│   ├── graph_tracker.py                      # v5 NEW: NetworkX + D3.js interactive graph export
│   ├── audit_logger.py                       # v5 NEW: SQLite + Markdown audit trails
│   ├── project_history.py                    # v5 NEW: SQLite persistence, continuation, forking
│   └── agents/
│       ├── __init__.py                       # v5 NEW imports added
│       ├── literature_scout.py               # v4 — unchanged
│       ├── gap_analyst.py                    # v4 — unchanged
│       ├── methodologist.py                  # v4 — unchanged
│       ├── academic_author.py                # v5: refactored for chunked section drafting
│       ├── domain_expert_council.py          # v5 NEW: 7 specialists with adversarial evaluation
│       ├── peer_review_board.py              # v5 NEW: Editor + 5 reviewers with Q1/Q2 standards
│       ├── conflict_resolution.py            # v5 NEW: structured debate & arbitration
│       └── experiment_agent.py               # v5 NEW: experiment design, notification, integration
├── tools/                                    # v4 — unchanged (ArXiv, OpenAlex, Semantic Scholar, Crossref, WebSearch, CodeInterpreter)
├── sample_outputs/                           # Generated papers and charts
├── uploads/                                  # Audit logs and user uploads
├── experiments/                              # v5 NEW: pending experiment notifications (JSON)
└── database/                                 # v5 NEW: SQLite databases (projects.db, audit.db)
```

## 🛠 Setup

```bash
pip install -r requirements.txt
```

### Configure your LLM

The app auto-discovers Ollama models. Default: `http://localhost:11434`.

In the sidebar, select:
- **Local LLM Model** — `ollama/llama3`, `ollama/mistral`, `ollama/deepseek-r1`, etc.
- **API Endpoint** — `http://localhost:11434` for Ollama, `http://localhost:1234` for LM Studio.

## 🖥 Running the App

```bash
streamlit run app.py
```

### v5 Enhanced Mode Toggle

In the sidebar, enable **🚀 v5 Enhanced Mode** to activate:
- Expert Council (7 specialists)
- Peer Review Board (Editor + 5 reviewers)
- Chunked Drafting (section-by-section generation)
- Experiment Design & Notifications
- Process Graph & Audit Logs
- Project History

When **disabled**, the app runs the original v4 stage workflow (consultation → gaps → methodology → author).

## 🔄 v5 Full Pipeline Flow

```
INIT
  → Stage 1: Literature Scout (ArXiv, OpenAlex, Semantic Scholar, Crossref)
  → Stage 2: Gap Analysis & Hypothesis Formation
  → Stage 3: Methodology & Investigation
  → Stage 4: Expert Council Evaluation (7 specialists score and dissent)
       → Conflict Resolution (if consensus < 0.60): structured debate rounds
  → Stage 5: Chunked Drafting (section-by-section, 800–1500 words each)
  → Stage 6: Peer Review Board (Editor + 5 reviewers vote)
       → ACCEPT / MINOR_REVISION → proceed
       → MAJOR_REVISION / REJECT → revision loop (max 5 iterations)
  → Stage 7: Experiment Assessment (if real-world validation needed)
       → PAUSE pipeline, notify user via experiments/pending_experiments.json
       → User performs lab work, submits results, pipeline resumes
  → Stage 8: Final Edit & Export
       → Interactive D3.js graph → sample_outputs/<project_id>_graph.html
       → Full Markdown audit log → uploads/<project_id>_COMPLETE.md
       → SQLite project snapshot → database/projects.db
       → Publication-ready paper → sample_outputs/<topic>_deliverable.md
```

## 🧠 Expert Council (7 Agents)

1. **LinguistExpert** — grammar, style, clarity, terminology, readability
2. **MathematicianExpert** — proofs, derivations, numerical accuracy, modeling
3. **PhysicistExpert** — laws, units, experimental design, consistency
4. **StatisticianExpert** — significance, confidence intervals, bias detection
5. **MethodologistExpert** — study design, reproducibility, ethics
6. **LogisticianExpert** — feasibility, resource constraints, scalability
7. **EpistemologistExpert** — logical consistency, falsifiability, assumptions

Each expert evaluates **independently**, can **dissent** (raise fundamental objections), and participates in **structured debate rounds** if consensus is low.

## 🔬 Peer Review Board (6 Agents)

- **EditorAgent** — Chief Editor, overall coherence & Q1 standard enforcement
- **MethodologyReviewer** — study design, data collection, reproducibility
- **LiteratureReviewer** — citation depth, gap analysis, scholarship
- **ResultsReviewer** — validity, statistical rigor, interpretation
- **ImpactReviewer** — practical applicability, societal value
- **NoveltyReviewer** — originality, theoretical advancement

Each reviewer issues a verdict: **ACCEPT**, **MINOR_REVISION**, **MAJOR_REVISION**, or **REJECT**. The Editor synthesizes these into a final editorial letter. If standards are not met, the paper loops back for revision.

## 📊 Outputs

| Output | Location | Description |
|--------|----------|-------------|
| **Paper** | `sample_outputs/<topic>_deliverable.md` | Final Markdown manuscript |
| **Graph** | `sample_outputs/<project_id>_graph.html` | Interactive D3.js force-directed graph |
| **Audit Log** | `uploads/<project_id>_COMPLETE.md` | Full timestamped Markdown audit |
| **Project DB** | `database/projects.db` | SQLite with all project snapshots |
| **Audit DB** | `database/audit.db` | SQLite with structured audit records |
| **Experiments** | `experiments/pending_experiments.json` | Pending experiment notifications |

## 📋 Project History & Continuation

The v5 `ProjectHistory` module automatically saves every project to `database/projects.db`.

- **Resume** — reload any past project and continue from its last stage
- **Fork** — create a new branch from an existing project snapshot
- **Reference** — link projects together (e.g., a follow-up study referencing the original)

All history is visible in the **📚 History** tab after running a v5 pipeline.

## ⚙ Configuration Tips

- **Local model too weak?** Use a larger model (e.g., `llama3.1:70b`, `mixtral:8x22b`) or lower the `chunk_size` in `academic_author.py`.
- **Debate too slow?** Lower `max_expert_debate_rounds` in `models.py` (default: 3).
- **Too strict?** Lower `peer_review_accept_threshold` in `models.py` (default: 0.75).
- **No experiments?** The Experiment Agent automatically skips topics that don't need empirical validation.

## 🧪 Experiment Workflow Example

When the pipeline detects that real-world validation is needed:

1. The **Experiment Agent** designs a protocol with variables, materials, procedure, and safety notes.
2. It writes the design to `experiments/pending_experiments.json` and **pauses the pipeline**.
3. You perform the lab/field/simulation work, collect results, and submit them back.
4. The agent **integrates your results** into the Results and Discussion sections.
5. The pipeline resumes to Peer Review and Final Edit.

## 📜 License

MIT — use, fork, and improve for your research pipeline.
