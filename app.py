import os
import time
import streamlit as st
import pandas as pd
from research_engine.orchestrator import ResearchOrchestrator
from research_engine.models import ResearchState
from research_engine.domain_engine import DomainIntelligenceEngine


# Configure Streamlit Page for Native Apple Dark Mode Aesthetic
st.set_page_config(
    page_title="Research Agent — Apple Dark OS",
    page_icon="🍏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling: Apple macOS Dark Mode / VisionOS Skin + Real-Time Timer + Document Pool
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

    /* Stopwatch Timer Banner */
    .apple-timer-banner {
        background: linear-gradient(145deg, #1C1C1E 0%, #101B2E 100%);
        border: 1px solid rgba(10, 132, 255, 0.4);
        border-radius: 16px;
        padding: 1.4rem 1.8rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(10, 132, 255, 0.15);
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }

    .apple-card {
        background: #1C1C1E;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        transition: all 0.2s ease-in-out;
    }
    .apple-card:hover {
        border-color: rgba(10, 132, 255, 0.4);
        box-shadow: 0 12px 35px rgba(10, 132, 255, 0.15);
    }
    
    .pool-card {
        background: linear-gradient(145deg, #1C1C1E 0%, #1C1A2E 100%);
        border: 1px solid rgba(175, 82, 222, 0.4);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(175, 82, 222, 0.12);
    }

    .status-card-apple {
        background: linear-gradient(145deg, #1C1C1E 0%, #121A2A 100%);
        border: 1px solid rgba(10, 132, 255, 0.3);
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(10, 132, 255, 0.1);
    }

    .gap-card-apple {
        background: linear-gradient(145deg, #1C1C1E 0%, #2A2012 100%);
        border: 1px solid rgba(255, 159, 10, 0.3);
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }
    
    .consultation-card {
        background: linear-gradient(145deg, #1C1C1E 0%, #152317 100%);
        border: 1px solid rgba(48, 209, 88, 0.4);
        border-radius: 16px;
        padding: 1.8rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(48, 209, 88, 0.12);
    }

    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
        background-color: #1C1C1E !important;
        color: #F5F5F7 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        padding: 0.6rem 1rem !important;
        font-size: 1rem !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #0A84FF !important;
        box-shadow: 0 0 0 2px rgba(10, 132, 255, 0.25) !important;
    }
    
    .stButton button[kind="primary"] {
        background: linear-gradient(180deg, #0A84FF 0%, #0070E5 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 14px rgba(10, 132, 255, 0.35) !important;
        transition: transform 0.1s ease, box-shadow 0.2s ease !important;
    }
    .stButton button[kind="primary"]:hover {
        background: linear-gradient(180deg, #2997FF 0%, #0A84FF 100%) !important;
        box-shadow: 0 6px 20px rgba(10, 132, 255, 0.5) !important;
        transform: translateY(-1px) !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1C1C1E !important;
        border-radius: 12px !important;
        padding: 4px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        gap: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 8px !important;
        color: #8E8E93 !important;
        font-weight: 500 !important;
        padding: 8px 16px !important;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2C2C2E !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
    }
    
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #0A84FF 0%, #30D158 100%) !important;
        border-radius: 10px !important;
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
        line-height: 1.6;
        box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);
    }
    
    .streamlit-expanderHeader {
        background-color: #1C1C1E !important;
        border-radius: 12px !important;
        color: #F5F5F7 !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    if "research_state" not in st.session_state:
        st.session_state.research_state = None
    if "workflow_stage" not in st.session_state:
        st.session_state.workflow_stage = "idle" # 'idle', 'retrieving', 'consultation', 'executing', 'completed'
    if "selected_topic" not in st.session_state:
        st.session_state.selected_topic = "Risk Mitigation Framework for Emerging Maritime Operations"


def render_sidebar():
    st.sidebar.markdown("## 🍏 System Settings")
    st.sidebar.markdown("<span style='color: #8E8E93; font-size: 0.85rem;'>Apple Dark OS • 'Prof' Academic Standards</span>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("### 🎯 Target Deliverable & Size")
    deliverable_choice = st.sidebar.selectbox(
        "Select Output Format & Word Count:",
        options=[
            "Full Academic Research Paper (~4,000 - 8,000 words / 15-25 pages)",
            "Extended Research Proposal / Grant Application (~2,500 - 5,000 words / 10-15 pages)",
            "PhD / Master's Thesis Chapter (~5,000 - 10,000 words / 20-35 pages)",
            "Systematic Literature Review (PRISMA Framework) (~3,500 - 7,000 words / 12-20 pages)",
            "Executive Research Outline & Methodology Plan (~1,500 - 3,000 words / 5-10 pages)",
            "Abstract & Executive Summary (~250 - 500 words / 1-2 pages)",
            "Peer Review Critique & Scientific Rebuttal Letter (~1,000 - 2,500 words / 4-8 pages)"
        ],
        index=0,
        help="The agent team dynamically adjusts section depth, headings, and analytical scope to match your chosen deliverable."
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🦙 AI Engine Source")
    model_choice = st.sidebar.selectbox(
        "Local LLM Model",
        options=[
            "ollama/llama3",
            "ollama/mistral",
            "ollama/qwen",
            "ollama/deepseek-r1",
            "lm-studio-local"
        ],
        index=0,
        help="Connects to Ollama on your machine. Auto-discovers installed model tags (e.g. llama3:8b) if exact name is not found!"
    )
    
    base_url = st.sidebar.text_input(
        "Local API Endpoint",
        value="http://localhost:11434",
        help="Default Ollama URL: http://localhost:11434. LM Studio: http://localhost:1234."
    )
    
    st.sidebar.markdown("### 🧠 Analytical Precision / Temperature")
    temperature = st.sidebar.slider(
        "Select Reasoning Mode:",
        min_value=0.1, max_value=1.0, value=0.2, step=0.1,
        help="Controls the mathematical and logical rigor vs exploratory creativity of the AI agents."
    )
    st.sidebar.markdown("""
    <div style="background-color: #1C1C1E; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 0.8rem; font-size: 0.82rem; color: #8E8E93; line-height: 1.4;">
        <strong style="color: #30D158;">0.1 – 0.3 | Strict Factual Rigor</strong><br>
        Recommended for 'Prof' standards. Zero creative drift, maximum analytical consistency.<br><br>
        <strong style="color: #0A84FF;">0.4 – 0.6 | Balanced Synthesis</strong><br>
        Ideal for literature integration and scientific argumentation.<br><br>
        <strong style="color: #FF9F0A;">0.7 – 1.0 | Exploratory Ideation</strong><br>
        Best for brainstorming novel hypotheses or grant proposals.
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚡ Execution Mode")
    st.sidebar.markdown("""
    <div style="background-color: #1C1C1E; border: 1px solid rgba(48, 209, 88, 0.4); border-radius: 12px; padding: 1rem; font-size: 0.88rem; color: #30D158;">
        <strong>100% Real Live Mode</strong><br>
        <span style="color: #F5F5F7;">Zero fake fallbacks or pre-canned demo strings. All literature is scraped live across 4 databases. Ensure Ollama is running!</span>
    </div>
    """, unsafe_allow_html=True)
    
    allow_code = st.sidebar.checkbox(
        "Allow Python Code Execution",
        value=True,
        help="Enables the Lead Methodologist agent to write and execute real Python scripts locally when appropriate."
    )
    
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

    return model_choice, base_url, temperature, deliverable_choice, allow_code


def render_header():
    st.markdown('<div class="apple-title">Autonomous Research Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="apple-subtitle">Powered by Role-Based CrewAI • 4 Free Academic Databases • 100% Real Scraping • "Prof" Academic Persona</div>', unsafe_allow_html=True)


def main():
    init_session_state()
    model_choice, base_url, temperature, deliverable_choice, allow_code = render_sidebar()
    render_header()

    # Topic Search Bar
    col1, col2 = st.columns([4, 1])
    with col1:
        topic_input = st.text_input(
            "Enter Research Topic or Scientific Challenge:",
            value=st.session_state.selected_topic,
            key="topic_input_field",
            placeholder="e.g. Risk Mitigation Framework for Emerging Maritime Operations..."
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        start_btn = st.button("✨ Start Research", type="primary", use_container_width=True)

    # 📂 RESEARCH THINKING, ANALYSIS & WRITING POOL (File Upload Suite)
    with st.expander("📂 Research Thinking, Analysis & Writing Pool (Upload Existing Drafts, Abstracts, or Ideas)", expanded=False):
        st.markdown("""
        <div class="pool-card">
            <h4 style="color: #AF52DE !important; margin-bottom: 0.4rem;">🔬 The Research Pool</h4>
            <p style="color: #F5F5F7; font-size: 0.95rem;">
                Transform the app into a collaborative academic powerhouse! Upload your existing abstracts, rough notes, research proposals, or data files. 
                The agent team will evaluate your document alongside scraped peer-reviewed literature.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col_p1, col_p2 = st.columns([1, 1])
        with col_p1:
            uploaded_files = st.file_uploader(
                "Upload Research Documents (.md, .txt, .csv, .json, .py):",
                accept_multiple_files=True,
                type=["md", "txt", "csv", "json", "py"],
                help="Upload plain text or markdown files containing your research notes or drafts."
            )
        with col_p2:
            pool_action = st.selectbox(
                "Select Research Pool Action:",
                options=[
                    "Think WITH the Draft (Expand, Refine & Build Upon)",
                    "Think AGAINST the Draft (Rigorous Peer Review Critique & Rebuttal)",
                    "Refine & Elevate to Top Journal Publication Standard",
                    "Integrate Scraped Empirical Evidence & Academic Citations"
                ],
                index=0,
                help="Directs how the agent team should evaluate and process your uploaded documents."
            )

    # Parse uploaded files content
    parsed_files_list = []
    if uploaded_files:
        for file in uploaded_files:
            try:
                content_str = file.read().decode("utf-8", errors="ignore")
                parsed_files_list.append({
                    "filename": file.name,
                    "content": content_str
                })
            except Exception as e:
                st.warning(f"Could not decode file {file.name}: {str(e)}")

    if start_btn and topic_input:
        st.session_state.selected_topic = topic_input
        st.session_state.selected_deliverable = deliverable_choice
        st.session_state.selected_pool_action = pool_action
        st.session_state.parsed_files = parsed_files_list
        st.session_state.workflow_stage = "retrieving"
        st.session_state.research_state = None

    # STAGE 1: Literature Retrieval across 4 Databases
    if st.session_state.workflow_stage == "retrieving":
        st.markdown("---")
        st.markdown("### 📡 Stage 1: Deep Scoping Literature & Classifying Discipline")
        
        timer_box = st.empty()
        progress_bar = st.progress(10, text="Querying ArXiv, OpenAlex, Semantic Scholar, and Crossref...")
        status_box = st.empty()
        log_box = st.empty()
        
        def update_ui_callback(current_state: ResearchState):
            elapsed_sec = time.time() - current_state.start_time
            elapsed_str = f"{int(elapsed_sec) // 60:02d}:{int(elapsed_sec) % 60:02d}"
            if current_state.progress_percentage > 5 and current_state.progress_percentage < 100:
                total_est = (elapsed_sec / (current_state.progress_percentage / 100.0))
                rem = max(0, int(total_est - elapsed_sec))
                eta_str = f"~{rem // 60:02d}:{rem % 60:02d}"
            else:
                eta_str = "Calculating..."

            timer_box.markdown(f"""
            <div class="apple-timer-banner">
                <div style="font-size: 0.88rem; color: #8E8E93; font-weight: 600; letter-spacing: 0.05em;">⏱️ ELAPSED TIME &amp; ETA TRACKER</div>
                <div style="font-size: 2.2rem; font-weight: 700; color: #30D158; font-family: 'SF Mono', monospace; margin: 4px 0;">
                    {elapsed_str} <span style="font-size: 1.2rem; color: #8E8E93; font-weight: 400;">| EST. REMAINING: {eta_str}</span>
                </div>
                <div style="font-size: 0.95rem; color: #0A84FF; font-weight: 500;">● Deep Real Scraping &amp; Analytical Reasoning in Progress...</div>
            </div>
            """, unsafe_allow_html=True)

            progress_bar.progress(
                current_state.progress_percentage,
                text=f"Current Workflow: {current_state.current_stage} ({current_state.progress_percentage}%)"
            )
            
            latest_log = current_state.logs[-1] if current_state.logs else None
            if latest_log:
                status_html = f"""
                <div class="status-card-apple">
                    <span style="color: #0A84FF; font-weight: 600; font-size: 0.9rem;">● ACTIVE AGENT ROLE</span><br>
                    <strong style="font-size: 1.2rem; color: #FFFFFF;">{latest_log.agent_name}</strong><br>
                    <span style="color: #F5F5F7; font-size: 1rem;">Action: {latest_log.action}</span><br>
                    <span style="color: #8E8E93; font-size: 0.88rem;">Details: {latest_log.details or 'Processing task...'}</span>
                </div>
                """
                status_box.markdown(status_html, unsafe_allow_html=True)
            
            logs_data = []
            for log in reversed(current_state.logs[-10:]):
                status_icon = "🟢" if log.status == "completed" else "🟡" if log.status == "running" else "🔴"
                logs_data.append(f"<span style='color:#636366;'>[{log.timestamp}]</span> {status_icon} <strong style='color:#0A84FF;'>[{log.agent_name}]</strong> ➔ <span style='color:#FFFFFF;'>{log.stage}:</span> {log.action}")
            
            log_box.markdown(f'<div class="apple-terminal">{"<br>".join(logs_data)}</div>', unsafe_allow_html=True)

        with st.spinner("Scraping up to 60 publications across 4 databases and synthesizing literature under 'Prof' standards..."):
            orchestrator = ResearchOrchestrator(model_name=model_choice, base_url=base_url, temperature=temperature)
            state = orchestrator.run_stage_1_literature(
                topic=st.session_state.selected_topic,
                target_deliverable=st.session_state.get("selected_deliverable", deliverable_choice),
                pool_action=st.session_state.get("selected_pool_action", pool_action),
                uploaded_files=st.session_state.get("parsed_files", parsed_files_list),
                allow_code_execution=allow_code,
                progress_callback=update_ui_callback
            )
            st.session_state.research_state = state
            st.session_state.workflow_stage = "consultation"
            st.rerun()

    # STAGE 2: Interactive User Consultation & Alignment Checkpoint
    if st.session_state.workflow_stage == "consultation" and st.session_state.research_state:
        state: ResearchState = st.session_state.research_state
        disc, rec_method, _ = DomainIntelligenceEngine.classify_domain_and_methodology(state.topic)
        
        st.markdown("---")
        st.markdown("""
        <div class="consultation-card">
            <h3 style="color: #30D158 !important; margin-bottom: 0.5rem;">🤝 Stage 2: Strategy Consultation & Alignment</h3>
            <p style="color: #F5F5F7; font-size: 1.05rem;">
                Before drafting your target deliverable (<strong>{}</strong>), let's confirm the exact direction. We scraped 
                <strong>{} verified peer-reviewed papers</strong> from OpenAlex, ArXiv, Semantic Scholar, and Crossref.
            </p>
            <p style="color: #8E8E93;">
                <strong>Identified Academic Discipline:</strong> <code style="color:#0A84FF; background:#0B0B0D; padding:4px 10px; border-radius:8px;">{}</code><br>
                <strong>Recommended Methodology:</strong> <code style="color:#30D158; background:#0B0B0D; padding:4px 10px; border-radius:8px;">{}</code>
            </p>
        </div>
        """.format(state.target_deliverable.split(" (")[0], len(state.extracted_papers), disc, rec_method.upper().replace('_', ' ')), unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            st.markdown("#### 1. Select Target Research Gap")
            if state.identified_gaps:
                gap_options = [f"[{g.gap_id}] {g.title}" for g in state.identified_gaps]
                selected_gap_idx = st.radio(
                    "Choose the scientific contradiction or gap you want to focus on:",
                    options=range(len(gap_options)),
                    format_func=lambda i: gap_options[i],
                    index=0
                )
                st.info(f"**Description:** {state.identified_gaps[selected_gap_idx].description}")
            else:
                st.warning("No structured gaps retrieved. The agent will proceed with general bibliometric analysis.")
                selected_gap_idx = 0

        with col_c2:
            st.markdown("#### 2. Confirm Investigation Methodology")
            method_list = [
                "qualitative_case_study",
                "systematic_literature_review",
                "comparative_meta_analysis",
                "statistical_survey_analysis",
                "theoretical_framework",
                "computational_simulation"
            ]
            default_idx = method_list.index(rec_method) if rec_method in method_list else 0
            
            selected_method = st.selectbox(
                "Select the methodological approach for Section 5 & 6:",
                options=method_list,
                index=default_idx,
                format_func=lambda m: m.upper().replace("_", " ")
            )
            
            st.markdown("#### 3. Custom Focus Emphasis (Optional)")
            user_note = st.text_input(
                "Add specific instructions or context for the authoring agent:",
                placeholder="e.g. Focus specifically on acoustic noise and marine radio protocols..."
            )

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ Confirm Strategy & Generate Publication-Ready Deliverable", type="primary", use_container_width=True):
            st.session_state.confirmed_gap_idx = selected_gap_idx
            st.session_state.confirmed_method = selected_method
            st.session_state.user_note = user_note
            st.session_state.workflow_stage = "executing"
            st.rerun()

    # STAGE 3 & 4: Execute Investigation & Draft Deliverable
    if st.session_state.workflow_stage == "executing" and st.session_state.research_state:
        st.markdown("---")
        st.markdown("### 📡 Stage 3 & 4: Executing Investigation & Drafting Citation-Backed Deliverable")
        
        timer_box = st.empty()
        progress_bar = st.progress(50, text="Executing investigation and writing citation-backed deliverable...")
        status_box = st.empty()
        log_box = st.empty()
        
        def update_ui_callback(current_state: ResearchState):
            elapsed_sec = time.time() - current_state.start_time
            elapsed_str = f"{int(elapsed_sec) // 60:02d}:{int(elapsed_sec) % 60:02d}"
            if current_state.progress_percentage > 5 and current_state.progress_percentage < 100:
                total_est = (elapsed_sec / (current_state.progress_percentage / 100.0))
                rem = max(0, int(total_est - elapsed_sec))
                eta_str = f"~{rem // 60:02d}:{rem % 60:02d}"
            else:
                eta_str = "Calculating..."

            timer_box.markdown(f"""
            <div class="apple-timer-banner">
                <div style="font-size: 0.88rem; color: #8E8E93; font-weight: 600; letter-spacing: 0.05em;">⏱️ ELAPSED TIME &amp; ETA TRACKER</div>
                <div style="font-size: 2.2rem; font-weight: 700; color: #30D158; font-family: 'SF Mono', monospace; margin: 4px 0;">
                    {elapsed_str} <span style="font-size: 1.2rem; color: #8E8E93; font-weight: 400;">| EST. REMAINING: {eta_str}</span>
                </div>
                <div style="font-size: 0.95rem; color: #0A84FF; font-weight: 500;">● Deep Real Scraping &amp; Analytical Reasoning in Progress...</div>
            </div>
            """, unsafe_allow_html=True)

            progress_bar.progress(
                current_state.progress_percentage,
                text=f"Current Workflow: {current_state.current_stage} ({current_state.progress_percentage}%)"
            )
            
            latest_log = current_state.logs[-1] if current_state.logs else None
            if latest_log:
                status_html = f"""
                <div class="status-card-apple">
                    <span style="color: #0A84FF; font-weight: 600; font-size: 0.9rem;">● ACTIVE AGENT ROLE</span><br>
                    <strong style="font-size: 1.2rem; color: #FFFFFF;">{latest_log.agent_name}</strong><br>
                    <span style="color: #F5F5F7; font-size: 1rem;">Action: {latest_log.action}</span><br>
                    <span style="color: #8E8E93; font-size: 0.88rem;">Details: {latest_log.details or 'Processing task...'}</span>
                </div>
                """
                status_box.markdown(status_html, unsafe_allow_html=True)
            
            logs_data = []
            for log in reversed(current_state.logs[-12:]):
                status_icon = "🟢" if log.status == "completed" else "🟡" if log.status == "running" else "🔴"
                logs_data.append(f"<span style='color:#636366;'>[{log.timestamp}]</span> {status_icon} <strong style='color:#0A84FF;'>[{log.agent_name}]</strong> ➔ <span style='color:#FFFFFF;'>{log.stage}:</span> {log.action}")
            
            log_box.markdown(f'<div class="apple-terminal">{"<br>".join(logs_data)}</div>', unsafe_allow_html=True)

        with st.spinner("Synthesizing citations, generating tables, and formatting academic Markdown under 'Prof' standards..."):
            orchestrator = ResearchOrchestrator(model_name=model_choice, base_url=base_url, temperature=temperature)
            final_state = orchestrator.run_stages_2_to_4(
                state=st.session_state.research_state,
                confirmed_gap_index=st.session_state.get("confirmed_gap_idx", 0),
                confirmed_methodology=st.session_state.get("confirmed_method", "qualitative_case_study"),
                user_emphasis=st.session_state.get("user_note", ""),
                progress_callback=update_ui_callback
            )
            st.session_state.research_state = final_state
            st.session_state.workflow_stage = "completed"
            progress_bar.progress(100, text="✅ Research Workflow Completed Successfully!")
            st.success("🎉 Publication-ready academic deliverable generated successfully! Check the detailed Apple OS inspection tabs below.")

    # Results & Inspection Tabs
    if st.session_state.workflow_stage == "completed" and st.session_state.research_state:
        state: ResearchState = st.session_state.research_state
        st.markdown("---")
        st.markdown("### 📑 Research Outputs & Artifacts Inspection")
        
        tab_logs, tab_lit, tab_gaps, tab_sim, tab_ms = st.tabs([
            "📡 Activity Audit",
            f"📚 Scraped Literature ({len(state.extracted_papers)})",
            f"🔍 Research Gaps ({len(state.identified_gaps)})",
            "🧪 Investigation Protocol",
            "📄 Publication-Ready Deliverable (.md)"
        ])

        # TAB 1: Activity Logs
        with tab_logs:
            st.markdown("#### Full Agent Execution Audit Log")
            log_df_data = [
                {
                    "Timestamp": l.timestamp,
                    "Agent Persona": l.agent_name,
                    "Stage": l.stage,
                    "Action Taken": l.action,
                    "Details": l.details or "",
                    "Status": l.status.upper()
                }
                for l in state.logs
            ]
            st.dataframe(pd.DataFrame(log_df_data), use_container_width=True)

        # TAB 2: Literature Review
        with tab_lit:
            st.markdown("#### Executive Literature Synthesis ('Prof' Standards)")
            if state.literature_summary:
                st.markdown(f'<div class="apple-card">{state.literature_summary}</div>', unsafe_allow_html=True)
                
            st.markdown(f"#### Verified Academic Papers across 4 Databases ({len(state.extracted_papers)} Retrieved)")
            for paper in state.extracted_papers:
                with st.expander(f"📄 [{paper.source}] {paper.title} ({paper.published_date}) — Citations: {paper.citation_count}"):
                    st.markdown(f"**Authors:** {', '.join(paper.authors)}")
                    st.markdown(f"**Abstract:** {paper.abstract}")
                    if paper.key_findings:
                        st.markdown(f"**Key Findings:** {paper.key_findings}")
                    if paper.url:
                        st.markdown(f"**Source URL:** [{paper.url}]({paper.url})")

        # TAB 3: Research Gaps
        with tab_gaps:
            st.markdown("#### Identified Research Gaps & Contradictions")
            for gap in state.identified_gaps:
                st.markdown(f"""
                <div class="gap-card-apple">
                    <h4 style="color: #FF9F0A !important; margin-bottom: 0.5rem;">🚨 [{gap.gap_id}] {gap.title}</h4>
                    <p style="color: #F5F5F7;"><strong>Description:</strong> {gap.description}</p>
                    <p style="color: #8E8E93;"><strong>Significance:</strong> {gap.significance}</p>
                    <p style="color: #0A84FF;"><strong>Verified Related Literature:</strong> {', '.join(gap.related_papers)}</p>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("#### Formulated Research Questions & Hypotheses ('Prof' Rigor)")
            for rq in state.research_questions:
                st.markdown(f"""
                <div class="apple-card" style="border-left: 4px solid #30D158;">
                    <h4 style="color: #30D158 !important;">🔬 [{rq.question_id}] {rq.question}</h4>
                    <p><strong>Scientific Hypothesis:</strong> {rq.hypothesis}</p>
                    <p><strong>Methodology Classification:</strong> <code style="color:#0A84FF; background:#1C1C1E; padding:2px 8px; border-radius:6px;">{rq.methodology_type.upper()}</code></p>
                    <p><strong>Proposed Study Design:</strong> {rq.proposed_investigation}</p>
                </div>
                """, unsafe_allow_html=True)

        # TAB 4: Investigation Protocol
        with tab_sim:
            st.markdown("#### Methodological & Empirical Investigation")
            if not state.simulation_results:
                st.info("No investigation was recorded.")
            else:
                for sim in state.simulation_results:
                    st.markdown(f"**Experiment / Investigation:** `{sim.experiment_name}` — Status: `{'SUCCESS' if sim.success else 'FAILED'}`")
                    st.markdown(f"**Summary Findings:** {sim.summary_findings}")
                    
                    if sim.chart_path and os.path.exists(sim.chart_path):
                        st.markdown("##### 📊 Comparative Empirical Visualization")
                        st.image(sim.chart_path, caption="Automated Investigation Chart", use_container_width=True)
                    
                    if sim.code_executed:
                        with st.expander("🐍 View Executed Python Code", expanded=True):
                            st.code(sim.code_executed, language="python")
                            
                    with st.expander("🖥️ Execution Output & Audit Metrics", expanded=False):
                        st.text(sim.stdout or "No stdout generated.")
                    if sim.stderr:
                        with st.expander("⚠️ Standard Error (stderr)", expanded=False):
                            st.error(sim.stderr)

        # TAB 5: Final Deliverable
        with tab_ms:
            st.markdown(f"#### 📄 Publication-Ready Deliverable: {state.target_deliverable.split(' (~')[0]} (.md)")
            
            col_dl1, col_dl2 = st.columns([1, 3])
            with col_dl1:
                st.download_button(
                    label="📥 Download Publication-Ready Deliverable (.md)",
                    data=state.final_manuscript_md,
                    file_name=f"{state.topic.lower().replace(' ', '_')}_deliverable.md",
                    mime="text/markdown",
                    type="primary",
                    use_container_width=True
                )
            with col_dl2:
                st.markdown("<span style='color:#8E8E93; line-height:2.5;'>Click to download the complete citation-backed academic Markdown deliverable directly to your PC.</span>", unsafe_allow_html=True)
                
            st.markdown("---")
            st.markdown(state.final_manuscript_md)
            
            with st.expander("📋 View Raw Markdown Source Code", expanded=False):
                st.code(state.final_manuscript_md, language="markdown")


if __name__ == "__main__":
    main()
