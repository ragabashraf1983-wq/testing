import os
import time
import streamlit as st
import pandas as pd
from research_engine.orchestrator import ResearchOrchestrator
from research_engine.models import ResearchState
from research_engine.domain_engine import DomainIntelligenceEngine
from research_engine.project_history import ProjectHistory
from research_engine.audit_logger import AuditLogger


st.set_page_config(
    page_title="Research Agent v5 — Apple Dark OS",
    page_icon="🍏",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Inter", "Segoe UI", Roboto, Helvetica, sans-serif !important;
        background-color: #0F0F11 !important;
        color: #F5F5F7 !important;
    }
    .stApp {
        background: radial-gradient(circle at 50% 0%, #1c1c22 0%, #0F0F11 75%) !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #161618 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem !important;
    }
    h1, h2, h3, h4 {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
    }
    .apple-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FFFFFF 0%, #8E8E93 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        letter-spacing: -0.03em;
    }
    .apple-subtitle {
        font-size: 1.05rem;
        color: #8E8E93;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    .apple-timer-banner {
        background: linear-gradient(145deg, #1C1C1E 0%, #101B2E 100%);
        border: 1px solid rgba(10, 132, 255, 0.4);
        border-radius: 16px;
        padding: 1.4rem 1.8rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(10, 132, 255, 0.15);
    }
    .apple-card {
        background: #1C1C1E;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }
    .apple-card:hover {
        border-color: rgba(10, 132, 255, 0.4);
    }
    .pool-card {
        background: linear-gradient(145deg, #1C1C1E 0%, #1C1A2E 100%);
        border: 1px solid rgba(175, 82, 222, 0.4);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .status-card-apple {
        background: linear-gradient(145deg, #1C1C1E 0%, #121A2A 100%);
        border: 1px solid rgba(10, 132, 255, 0.3);
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
    }
    .gap-card-apple {
        background: linear-gradient(145deg, #1C1C1E 0%, #2A2012 100%);
        border: 1px solid rgba(255, 159, 10, 0.3);
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
    }
    .consultation-card {
        background: linear-gradient(145deg, #1C1C1E 0%, #152317 100%);
        border: 1px solid rgba(48, 209, 88, 0.4);
        border-radius: 16px;
        padding: 1.8rem;
    }
    .expert-card {
        background: linear-gradient(145deg, #1C1C1E 0%, #1A1A2E 100%);
        border: 1px solid rgba(52, 152, 219, 0.3);
        border-radius: 16px;
        padding: 1.2rem;
    }
    .peer-card {
        background: linear-gradient(145deg, #1C1C1E 0%, #2C1A2E 100%);
        border: 1px solid rgba(142, 68, 173, 0.3);
        border-radius: 16px;
        padding: 1.2rem;
    }
    .llm-warning {
        background: linear-gradient(145deg, #2C1A12 0%, #1A1010 100%);
        border: 1px solid rgba(255, 69, 58, 0.5);
        border-radius: 12px;
        padding: 1rem;
        color: #FF453A;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
        background-color: #1C1C1E !important;
        color: #F5F5F7 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
    }
    .stButton button[kind="primary"] {
        background: linear-gradient(180deg, #0A84FF 0%, #0070E5 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #0A84FF 0%, #30D158 100%) !important;
    }
    .apple-terminal {
        font-family: "SF Mono", "Consolas", "Fira Code", monospace;
        font-size: 0.88rem;
        background-color: #0B0B0D;
        color: #30D158;
        padding: 1.2rem;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        max-height: 380px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    if "research_state" not in st.session_state:
        st.session_state.research_state = None
    if "workflow_stage" not in st.session_state:
        st.session_state.workflow_stage = "idle"
    if "selected_topic" not in st.session_state:
        st.session_state.selected_topic = "Risk Mitigation Framework for Emerging Maritime Operations"
    if "v5_mode" not in st.session_state:
        st.session_state.v5_mode = True
    if "llm_provider" not in st.session_state:
        st.session_state.llm_provider = "Ollama (Local)"


def render_sidebar():
    st.sidebar.markdown("## 🍏 System Settings")
    
    v5_mode = st.sidebar.toggle("🚀 v5 Enhanced Mode", value=st.session_state.v5_mode)
    st.session_state.v5_mode = v5_mode

    # LLM Provider Selection
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🤖 LLM Provider")
    provider = st.sidebar.selectbox(
        "Select AI Engine",
        options=[
            "Ollama (Local)",
            "OpenAI (Cloud)",
            "Anthropic Claude (Cloud)",
            "LM Studio / LocalAI (OpenAI-compatible)",
        ],
        index=0,
        help="Cloud models (OpenAI/Anthropic) produce much more reliable structured JSON and long-form text."
    )
    st.session_state.llm_provider = provider

    # Provider-specific config
    api_key = None
    base_url = "http://localhost:11434"
    model_name = "ollama/llama3"

    if provider == "Ollama (Local)":
        model_name = st.sidebar.selectbox(
            "Local Model",
            options=[
                "ollama/llama3",
                "ollama/llama3.1",
                "ollama/llama3.1:70b",
                "ollama/mistral",
                "ollama/mixtral",
                "ollama/qwen",
                "ollama/deepseek-r1",
            ],
            index=0,
            help="⚠️ Small models (8B) often fail at structured JSON. Use 70B+ for best results."
        )
        base_url = st.sidebar.text_input("Ollama URL", value="http://localhost:11434")
        
        if "70b" not in model_name and ":8b" in model_name or "llama3" in model_name and "70b" not in model_name:
            st.sidebar.markdown("""
            <div class="llm-warning">
                ⚠️ <strong>Small Model Warning</strong><br>
                {model} may fail to produce structured JSON reliably.<br>
                Recommend: llama3.1:70b, mixtral, or a cloud model.
            </div>
            """.format(model=model_name.split("/")[-1]), unsafe_allow_html=True)

    elif provider == "OpenAI (Cloud)":
        model_name = st.sidebar.selectbox(
            "OpenAI Model",
            options=["openai/gpt-4o", "openai/gpt-4o-mini", "openai/gpt-4-turbo"],
            index=0,
        )
        api_key = st.sidebar.text_input("OpenAI API Key", type="password", help="Your API key is not stored.")
        base_url = "https://api.openai.com/v1"

    elif provider == "Anthropic Claude (Cloud)":
        model_name = st.sidebar.selectbox(
            "Anthropic Model",
            options=["anthropic/claude-3-5-sonnet-20241022", "anthropic/claude-3-opus-20240229"],
            index=0,
        )
        api_key = st.sidebar.text_input("Anthropic API Key", type="password", help="Your API key is not stored.")
        base_url = "https://api.anthropic.com"

    elif provider == "LM Studio / LocalAI (OpenAI-compatible)":
        model_name = st.sidebar.text_input("Model Name", value="local-model")
        base_url = st.sidebar.text_input("Base URL", value="http://localhost:1234/v1")
        api_key = st.sidebar.text_input("API Key (if required)", type="password")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎯 Target Deliverable & Size")
    deliverable_choice = st.sidebar.selectbox(
        "Select Output Format",
        options=[
            "Full Academic Research Paper (~4,000 - 8,000 words)",
            "Extended Research Proposal / Grant (~2,500 - 5,000 words)",
            "PhD / Master's Thesis Chapter (~5,000 - 10,000 words)",
            "Systematic Literature Review (~3,500 - 7,000 words)",
            "Executive Outline & Methodology (~1,500 - 3,000 words)",
            "Abstract & Executive Summary (~250 - 500 words)",
            "Peer Review Critique (~1,000 - 2,500 words)",
        ],
        index=0,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧠 Temperature / Creativity")
    temperature = st.sidebar.slider(
        "Reasoning Mode",
        min_value=0.1, max_value=1.0, value=0.2, step=0.1,
    )
    st.sidebar.markdown("""
    <div style="background-color: #1C1C1E; border-radius: 10px; padding: 0.8rem; font-size: 0.82rem; color: #8E8E93;">
        <strong style="color: #30D158;">0.1 – 0.3</strong> Strict Factual Rigor<br>
        <strong style="color: #0A84FF;">0.4 – 0.6</strong> Balanced Synthesis<br>
        <strong style="color: #FF9F0A;">0.7 – 1.0</strong> Exploratory Ideation
    </div>
    """, unsafe_allow_html=True)

    allow_code = st.sidebar.checkbox("Allow Python Code Execution", value=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📑 Instant Test Topics")
    if st.sidebar.button("🚢 Maritime Risk Mitigation", use_container_width=True):
        st.session_state.selected_topic = "Risk Mitigation Framework for Emerging Maritime Operations"
        st.session_state.workflow_stage = "idle"
    if st.sidebar.button("⚡ Renewable Energy Grid AI", use_container_width=True):
        st.session_state.selected_topic = "AI-Driven Optimization of Renewable Energy Grids"
        st.session_state.workflow_stage = "idle"
    if st.sidebar.button("🧬 Quantum Protein Folding", use_container_width=True):
        st.session_state.selected_topic = "Quantum Computing Applications in Protein Folding"
        st.session_state.workflow_stage = "idle"

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 Project History")
    try:
        ph = ProjectHistory()
        projects = ph.list_projects()
        if projects:
            for p in projects[:5]:
                st.sidebar.markdown(f"<span style='font-size:0.8rem; color:#8E8E93;'>• {p['title'][:30]} ({p['status']})</span>", unsafe_allow_html=True)
        else:
            st.sidebar.markdown("<span style='font-size:0.8rem; color:#636366;'>No saved projects yet.</span>", unsafe_allow_html=True)
    except Exception:
        pass

    return model_name, base_url, temperature, deliverable_choice, allow_code, api_key, v5_mode


def render_header():
    st.markdown('<div class="apple-title">Autonomous Research Agent v5</div>', unsafe_allow_html=True)
    st.markdown('<div class="apple-subtitle">Expert Council • Peer Review Board • Chunked Drafting • Process Graph • Audit Trail</div>', unsafe_allow_html=True)


def _build_ui_callback(timer_box, progress_bar, status_box, log_box, max_pct=100):
    def update_ui_callback(current_state: ResearchState):
        elapsed_sec = time.time() - current_state.start_time
        elapsed_str = f"{int(elapsed_sec) // 60:02d}:{int(elapsed_sec) % 60:02d}"
        if current_state.progress_percentage > 5 and current_state.progress_percentage < max_pct:
            total_est = (elapsed_sec / (current_state.progress_percentage / 100.0))
            rem = max(0, int(total_est - elapsed_sec))
            eta_str = f"~{rem // 60:02d}:{rem % 60:02d}"
        else:
            eta_str = "Calculating..."

        timer_box.markdown(f"""
        <div class="apple-timer-banner">
            <div style="font-size: 0.88rem; color: #8E8E93; font-weight: 600;">⏱️ ELAPSED TIME & ETA</div>
            <div style="font-size: 2.2rem; font-weight: 700; color: #30D158; font-family: 'SF Mono', monospace; margin: 4px 0;">
                {elapsed_str} <span style="font-size: 1.2rem; color: #8E8E93; font-weight: 400;">| EST: {eta_str}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        progress_bar.progress(
            min(current_state.progress_percentage, max_pct),
            text=f"Current: {current_state.current_stage} ({current_state.progress_percentage}%)"
        )
        
        latest_log = current_state.logs[-1] if current_state.logs else None
        if latest_log:
            status_color = "#FF453A" if latest_log.status == "error" else "#FF9F0A" if latest_log.status == "warning" else "#0A84FF"
            status_html = f"""
            <div class="status-card-apple">
                <span style="color: {status_color}; font-weight: 600;">● {latest_log.agent_name}</span><br>
                <strong style="font-size: 1.2rem; color: #FFFFFF;">{latest_log.action}</strong><br>
                <span style="color: #8E8E93; font-size: 0.88rem;">{latest_log.details or 'Processing...'}</span>
            </div>
            """
            status_box.markdown(status_html, unsafe_allow_html=True)
        
        logs_data = []
        for log in reversed(current_state.logs[-12:]):
            status_icon = "🟢" if log.status == "completed" else "🟡" if log.status == "running" else "🔴" if log.status == "error" else "🟠"
            logs_data.append(f"<span style='color:#636366;'>[{log.timestamp}]</span> {status_icon} <strong style='color:#0A84FF;'>[{log.agent_name}]</strong> ➔ {log.action}")
        
        log_box.markdown(f'<div class="apple-terminal">{"<br>".join(logs_data)}</div>', unsafe_allow_html=True)
    return update_ui_callback


def main():
    init_session_state()
    model_choice, base_url, temperature, deliverable_choice, allow_code, api_key, v5_mode = render_sidebar()
    render_header()

    col1, col2 = st.columns([4, 1])
    with col1:
        topic_input = st.text_input(
            "Enter Research Topic:",
            value=st.session_state.selected_topic,
            key="topic_input_field",
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        start_btn = st.button("✨ Start Research", type="primary", use_container_width=True)

    with st.expander("📂 Research Pool (Upload Drafts)", expanded=False):
        st.markdown('<div class="pool-card"><h4>🔬 Research Pool</h4><p>Upload existing abstracts, notes, or data files.</p></div>', unsafe_allow_html=True)
        col_p1, col_p2 = st.columns([1, 1])
        with col_p1:
            uploaded_files = st.file_uploader("Upload Documents:", accept_multiple_files=True, type=["md", "txt", "csv", "json", "py"])
        with col_p2:
            pool_action = st.selectbox("Pool Action:", options=[
                "Think WITH the Draft (Expand & Refine)",
                "Think AGAINST the Draft (Rigorous Critique)",
                "Refine & Elevate to Top Journal Standard",
                "Integrate Scraped Evidence & Citations",
            ], index=0)

    parsed_files_list = []
    if uploaded_files:
        for file in uploaded_files:
            try:
                content_str = file.read().decode("utf-8", errors="ignore")
                parsed_files_list.append({"filename": file.name, "content": content_str})
            except Exception as e:
                st.warning(f"Could not decode file {file.name}: {str(e)}")

    if start_btn and topic_input:
        st.session_state.selected_topic = topic_input
        st.session_state.selected_deliverable = deliverable_choice
        st.session_state.selected_pool_action = pool_action
        st.session_state.parsed_files = parsed_files_list
        st.session_state.workflow_stage = "retrieving"
        st.session_state.research_state = None

    # STAGE: Literature Retrieval
    if st.session_state.workflow_stage == "retrieving":
        st.markdown("---")
        st.markdown("### 📡 Stage 1: Deep Literature Scoping")
        
        timer_box = st.empty()
        progress_bar = st.progress(10, text="Querying ArXiv, OpenAlex, Semantic Scholar, Crossref...")
        status_box = st.empty()
        log_box = st.empty()
        
        update_ui_callback = _build_ui_callback(timer_box, progress_bar, status_box, log_box)

        with st.spinner("Scraping literature..."):
            orchestrator = ResearchOrchestrator(
                model_name=model_choice,
                base_url=base_url,
                temperature=temperature,
                api_key=api_key,
            )
            state = orchestrator.run_stage_1_literature(
                topic=st.session_state.selected_topic,
                target_deliverable=st.session_state.get("selected_deliverable", deliverable_choice),
                pool_action=st.session_state.get("selected_pool_action", pool_action),
                uploaded_files=st.session_state.get("parsed_files", parsed_files_list),
                allow_code_execution=allow_code,
                progress_callback=update_ui_callback,
            )
            st.session_state.research_state = state
            if v5_mode:
                st.session_state.workflow_stage = "executing_v5"
            else:
                st.session_state.workflow_stage = "consultation"
            st.rerun()

    # v5 Full Pipeline
    if st.session_state.workflow_stage == "executing_v5" and st.session_state.research_state:
        st.markdown("---")
        st.markdown("### 🚀 v5 Full Pipeline: Expert Council • Peer Review • Chunked Drafting • Audit")
        
        timer_box = st.empty()
        progress_bar = st.progress(25, text="Initializing v5 pipeline...")
        status_box = st.empty()
        log_box = st.empty()
        
        update_ui_callback = _build_ui_callback(timer_box, progress_bar, status_box, log_box, max_pct=99)

        with st.spinner("Running v5 pipeline..."):
            orchestrator = ResearchOrchestrator(
                model_name=model_choice,
                base_url=base_url,
                temperature=temperature,
                api_key=api_key,
            )
            final_state = orchestrator.run_v5_pipeline(
                topic=st.session_state.selected_topic,
                target_deliverable=st.session_state.get("selected_deliverable", deliverable_choice),
                pool_action=st.session_state.get("selected_pool_action", pool_action),
                uploaded_files=st.session_state.get("parsed_files", parsed_files_list),
                allow_code_execution=allow_code,
                progress_callback=update_ui_callback,
            )
            st.session_state.research_state = final_state
            st.session_state.workflow_stage = "completed"
            progress_bar.progress(100, text="✅ v5 Complete!")
            
            if final_state.status == "llm_quality_warning":
                st.error("⚠️ LLM QUALITY WARNING: The model produced weak/empty responses. Please switch to a stronger model (GPT-4o, Claude-3.5, or llama3.1:70b+) and retry.")
            elif final_state.status == "drafting_failed":
                st.error("⚠️ DRAFTING FAILED: The LLM could not generate paper sections. Please use a more powerful model.")
            else:
                st.success("🎉 v5 complete! Check all tabs below.")

    # v4 Consultation
    if st.session_state.workflow_stage == "consultation" and st.session_state.research_state:
        state = st.session_state.research_state
        disc, rec_method, _ = DomainIntelligenceEngine.classify_domain_and_methodology(state.topic)
        
        st.markdown("---")
        st.markdown('<div class="consultation-card"><h3>🤝 Stage 2: Strategy Consultation</h3></div>', unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            if state.identified_gaps:
                gap_options = [f"[{g.gap_id}] {g.title}" for g in state.identified_gaps]
                selected_gap_idx = st.radio("Select Target Gap:", options=range(len(gap_options)), format_func=lambda i: gap_options[i], index=0)
            else:
                selected_gap_idx = 0
        with col_c2:
            method_list = ["qualitative_case_study", "systematic_literature_review", "comparative_meta_analysis", "statistical_survey_analysis", "theoretical_framework", "computational_simulation"]
            default_idx = method_list.index(rec_method) if rec_method in method_list else 0
            selected_method = st.selectbox("Methodology:", options=method_list, index=default_idx, format_func=lambda m: m.upper().replace("_", " "))
            user_note = st.text_input("Custom Focus:", placeholder="e.g. Focus on acoustic noise...")

        if st.button("⚡ Confirm Strategy & Generate", type="primary", use_container_width=True):
            st.session_state.confirmed_gap_idx = selected_gap_idx
            st.session_state.confirmed_method = selected_method
            st.session_state.user_note = user_note
            st.session_state.workflow_stage = "executing"
            st.rerun()

    # v4 Execution
    if st.session_state.workflow_stage == "executing" and st.session_state.research_state:
        st.markdown("---")
        st.markdown("### 📡 Stage 3 & 4: Investigation & Drafting")
        
        timer_box = st.empty()
        progress_bar = st.progress(50, text="Executing...")
        status_box = st.empty()
        log_box = st.empty()
        
        update_ui_callback = _build_ui_callback(timer_box, progress_bar, status_box, log_box)

        with st.spinner("Synthesizing..."):
            orchestrator = ResearchOrchestrator(
                model_name=model_choice,
                base_url=base_url,
                temperature=temperature,
                api_key=api_key,
            )
            final_state = orchestrator.run_stages_2_to_4(
                state=st.session_state.research_state,
                confirmed_gap_index=st.session_state.get("confirmed_gap_idx", 0),
                confirmed_methodology=st.session_state.get("confirmed_method", "qualitative_case_study"),
                user_emphasis=st.session_state.get("user_note", ""),
                progress_callback=update_ui_callback,
            )
            st.session_state.research_state = final_state
            st.session_state.workflow_stage = "completed"
            progress_bar.progress(100, text="✅ Complete!")
            st.success("🎉 Done! Check tabs below.")

    # Results Tabs
    if st.session_state.workflow_stage == "completed" and st.session_state.research_state:
        state = st.session_state.research_state
        st.markdown("---")
        st.markdown("### 📑 Research Outputs")
        
        # LLM Quality Warning Banner
        if state.status in ("llm_quality_warning", "drafting_failed"):
            st.error("⚠️ This run produced weak/empty outputs due to LLM limitations. Results below may be incomplete. Use a stronger model and retry.")
        elif any(er.score == 0.5 and not er.dissent for er in state.expert_reviews):
            st.warning("⚠️ Expert Council detected fallback scores (0.5) — LLM may not be powerful enough for structured evaluation. Consider upgrading your model.")

        tab_labels = [
            "📡 Activity Audit",
            f"📚 Literature ({len(state.extracted_papers)})",
            f"🔍 Gaps ({len(state.identified_gaps)})",
            "🧪 Investigation",
            "📄 Deliverable (.md)",
        ]
        if v5_mode or state.expert_reviews:
            tab_labels.extend([
                f"🧠 Expert Council ({len(state.expert_reviews)})",
                f"🔬 Peer Review ({len(state.peer_reviews)})",
                f"🧪 Experiments ({len(state.experiments)})",
                "🕸️ Process Graph",
                "📋 Audit Log",
                "📚 History",
            ])
        
        tabs = st.tabs(tab_labels)
        tab_idx = 0

        with tabs[tab_idx]:
            tab_idx += 1
            st.markdown("#### Full Agent Execution Audit Log")
            log_df_data = [
                {"Timestamp": l.timestamp, "Agent": l.agent_name, "Stage": l.stage, "Action": l.action, "Details": l.details or "", "Status": l.status.upper()}
                for l in state.logs
            ]
            st.dataframe(pd.DataFrame(log_df_data), use_container_width=True)
            # Show any warnings/errors prominently
            errors = [l for l in state.logs if l.status in ("error", "warning")]
            if errors:
                st.markdown("#### ⚠️ Warnings & Errors")
                for e in errors:
                    color = "#FF453A" if e.status == "error" else "#FF9F0A"
                    st.markdown(f"<div style='background:#1C1C1E;border-left:4px solid {color};padding:8px 12px;border-radius:4px;margin:4px 0;'><strong>{e.agent_name}</strong> — {e.action}<br><span style='color:#8E8E93;'>{e.details}</span></div>", unsafe_allow_html=True)

        with tabs[tab_idx]:
            tab_idx += 1
            if state.literature_summary:
                st.markdown(f'<div class="apple-card">{state.literature_summary}</div>', unsafe_allow_html=True)
            for paper in state.extracted_papers:
                with st.expander(f"📄 [{paper.source}] {paper.title} ({paper.published_date}) — Citations: {paper.citation_count}"):
                    st.markdown(f"**Authors:** {', '.join(paper.authors)}")
                    st.markdown(f"**Abstract:** {paper.abstract}")
                    if paper.url:
                        st.markdown(f"**Source:** [{paper.url}]({paper.url})")

        with tabs[tab_idx]:
            tab_idx += 1
            for gap in state.identified_gaps:
                st.markdown(f"""
                <div class="gap-card-apple">
                    <h4 style="color: #FF9F0A !important;">🚨 [{gap.gap_id}] {gap.title}</h4>
                    <p>{gap.description}</p>
                    <p style="color: #8E8E93;"><strong>Significance:</strong> {gap.significance}</p>
                </div>
                """, unsafe_allow_html=True)
            for rq in state.research_questions:
                st.markdown(f"""
                <div class="apple-card" style="border-left: 4px solid #30D158;">
                    <h4 style="color: #30D158 !important;">🔬 [{rq.question_id}] {rq.question}</h4>
                    <p><strong>Hypothesis:</strong> {rq.hypothesis}</p>
                    <p><strong>Method:</strong> <code>{rq.methodology_type.upper()}</code></p>
                </div>
                """, unsafe_allow_html=True)

        with tabs[tab_idx]:
            tab_idx += 1
            if not state.simulation_results:
                st.info("No investigation recorded.")
            else:
                for sim in state.simulation_results:
                    st.markdown(f"**Experiment:** `{sim.experiment_name}` — Status: `{'SUCCESS' if sim.success else 'FAILED'}`")
                    st.markdown(f"**Findings:** {sim.summary_findings}")
                    if sim.chart_path and os.path.exists(sim.chart_path):
                        st.image(sim.chart_path, caption="Chart", use_container_width=True)
                    if sim.code_executed:
                        with st.expander("🐍 Code", expanded=True):
                            st.code(sim.code_executed, language="python")
                    with st.expander("🖥️ Output"):
                        st.text(sim.stdout or "No output.")
                    if sim.stderr:
                        st.error(sim.stderr)

        with tabs[tab_idx]:
            tab_idx += 1
            st.markdown(f"#### 📄 Deliverable: {state.target_deliverable.split(' (~')[0]}")
            col_dl1, col_dl2 = st.columns([1, 3])
            with col_dl1:
                st.download_button(
                    label="📥 Download (.md)",
                    data=state.final_manuscript_md,
                    file_name=f"{state.topic.lower().replace(' ', '_')}_deliverable.md",
                    mime="text/markdown",
                    type="primary",
                    use_container_width=True,
                )
            with col_dl2:
                st.markdown(f"<span style='color:#8E8E93;'>{len(state.final_manuscript_md)} characters</span>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown(state.final_manuscript_md)

        if v5_mode or state.expert_reviews:
            with tabs[tab_idx]:
                tab_idx += 1
                st.markdown("#### 🧠 Domain Expert Council (7 Specialists)")
                if not state.expert_reviews:
                    st.info("No expert evaluations. Enable v5 mode.")
                else:
                    for er in state.expert_reviews:
                        dissent_badge = "<span style='color:#e74c3c;'>⚠️ DISSENT</span>" if er.dissent else "<span style='color:#30D158;'>✅ CONCURS</span>"
                        llm_warning = "<span style='color:#FF9F0A;'>⚠️ FALLBACK SCORE</span>" if er.score == 0.5 and not er.dissent else ""
                        st.markdown(f"""
                        <div class="expert-card">
                            <h4 style="color: #3498db !important;">🎓 {er.expert_name}</h4>
                            <p style="color: #8E8E93; font-size: 0.9rem;">{er.domain}</p>
                            <p>Score: <strong>{er.score:.2f}</strong> | Confidence: <strong>{er.confidence:.2f}</strong> | {dissent_badge} {llm_warning}</p>
                            {f'<p style="color:#e74c3c;"><strong>Dissent:</strong> {er.dissent_reason}</p>' if er.dissent else ''}
                            <details><summary style="color:#0A84FF;">Criticisms ({len(er.criticisms)})</summary><ul>{''.join(f'<li>{c}</li>' for c in er.criticisms)}</ul></details>
                            <details><summary style="color:#30D158;">Suggestions ({len(er.suggestions)})</summary><ul>{''.join(f'<li>{s}</li>' for s in er.suggestions)}</ul></details>
                        </div>
                        """, unsafe_allow_html=True)

            with tabs[tab_idx]:
                tab_idx += 1
                st.markdown("#### 🔬 Peer Review Board")
                if not state.peer_reviews:
                    st.info("No peer reviews. Enable v5 mode.")
                else:
                    for pr in state.peer_reviews:
                        color = {"ACCEPT": "#30D158", "MINOR_REVISION": "#FF9F0A", "MAJOR_REVISION": "#e74c3c", "REJECT": "#c0392b"}.get(pr.verdict, "#8E8E93")
                        llm_warning = "<span style='color:#FF9F0A;'>⚠️ FALLBACK SCORE</span>" if pr.score == 0.5 else ""
                        st.markdown(f"""
                        <div class="peer-card">
                            <h4 style="color: {color} !important;">📋 Round {pr.round} — {pr.reviewer}</h4>
                            <p>Verdict: <strong style="color:{color};">{pr.verdict}</strong> | Score: <strong>{pr.score:.2f}</strong> {llm_warning}</p>
                            <p style="color: #F5F5F7;">{pr.comments}</p>
                            {f'<p style="color:#e74c3c;"><strong>Issues:</strong> {pr.specific_issues}</p>' if pr.specific_issues else ''}
                        </div>
                        """, unsafe_allow_html=True)

            with tabs[tab_idx]:
                tab_idx += 1
                st.markdown("#### 🧪 Experiments")
                if not state.experiments:
                    st.info("No experiments required.")
                else:
                    for exp in state.experiments:
                        status_color = "#30D158" if exp.get("status") == "COMPLETED" else "#FF9F0A" if exp.get("status") == "PENDING_USER" else "#8E8E93"
                        st.markdown(f"""
                        <div class="apple-card" style="border-left: 4px solid {status_color};">
                            <h4 style="color: {status_color} !important;">🔬 {exp.get('title', 'Untitled')}</h4>
                            <p><strong>ID:</strong> <code>{exp.get('experiment_id', 'N/A')}</code></p>
                            <p><strong>Status:</strong> <span style="color:{status_color};">{exp.get('status', 'N/A')}</span></p>
                            <p><strong>Objective:</strong> {exp.get('objective', '')}</p>
                            <p><strong>Hypothesis:</strong> {exp.get('hypothesis', '')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        if exp.get("status") == "PENDING_USER":
                            st.warning(f"⚠️ USER ACTION REQUIRED: Perform experiment {exp.get('experiment_id')} and submit results.")

            with tabs[tab_idx]:
                tab_idx += 1
                st.markdown("#### 🕸️ Process Network Graph")
                if state.graph_path and os.path.exists(state.graph_path):
                    with open(state.graph_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
                    st.components.v1.html(html_content, height=600, scrolling=True)
                    with open(state.graph_path, "rb") as f:
                        st.download_button("📥 Download Graph (.html)", f, file_name=f"{state.project_id}_graph.html", mime="text/html")
                else:
                    st.info("Graph not yet generated.")

            with tabs[tab_idx]:
                tab_idx += 1
                st.markdown("#### 📋 Full Audit Log")
                if state.audit_log_path and os.path.exists(state.audit_log_path):
                    with open(state.audit_log_path, "r", encoding="utf-8") as f:
                        audit_content = f.read()
                    st.text_area("Audit Log", audit_content, height=600)
                    with open(state.audit_log_path, "rb") as f:
                        st.download_button("📥 Download Audit (.md)", f, file_name=f"{state.project_id}_COMPLETE.md", mime="text/markdown")
                else:
                    st.info("Audit log not yet generated.")

            with tabs[tab_idx]:
                tab_idx += 1
                st.markdown("#### 📚 Project History")
                try:
                    ph = ProjectHistory()
                    projects = ph.list_projects()
                    if projects:
                        df = pd.DataFrame(projects)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No saved projects yet.")
                except Exception as e:
                    st.error(f"Could not load history: {e}")


if __name__ == "__main__":
    main()
