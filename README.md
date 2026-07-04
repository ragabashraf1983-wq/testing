# 🍏 Autonomous Academic Research Agent — Apple Dark OS Edition (for Windows)
### Powered by Role-Based CrewAI Architecture, Free Academic APIs, & Open-Source Local LLMs

An end-to-end autonomous multi-agent research framework engineered specifically for **local Windows execution using 100% free and open-source software**, presented with a sleek **Apple Dark Mode ("SF Pro / VisionOS" aesthetic)** and **Native Desktop App Mode** windowing.

By simply naming a topic in the minimalist dark UI, the agent team autonomously searches academic literature, synthesizes state-of-the-art findings, identifies critical research gaps, formulates testable scientific hypotheses, executes computational investigations (writing and running Python code for mathematical modeling and data simulations), and outputs a formal, publication-ready academic manuscript formatted in **Markdown (`.md`)**.

---

## 🌟 Key Features & Architectural Highlights

* 🍏 **Apple Dark Mode Skin for Windows (`app.py`)**: Designed with deep system grays (`#0F0F11`, `#1C1C1E`), subtle glassmorphic borders, Apple system blue highlights (`#0A84FF`), smooth rounded pills, and clean typography.
* 🪟 **Native Desktop App Mode Launcher (`Start_Research_Agent.bat`)**: Automatically opens Microsoft Edge or Google Chrome in **Dedicated App Mode (`--app=http://localhost:8501`)**. This removes browser address bars and toolbars, giving you a clean, standalone native desktop application feel on Windows!
* 📦 **Shareable Portable Software Bundle (`Autonomous_Research_Agent_Portable.zip`)**: A self-contained 254 KB portable distribution. Copy this zip file anywhere (USB drive, email, cloud storage); anyone on Windows can unzip it and double-click `Start_Research_Agent.bat` to run the software immediately with zero setup hassles!
* 🦙 **100% Free & Local LLM Support (`llm_client.py`)**: Natively integrated with **Ollama** (`llama3`, `mistral`, `qwen`, `deepseek-r1`) and OpenAI-compatible local endpoints (LM Studio, LocalAI). Zero paid API keys required.
* 📚 **Free Academic APIs Integration (`tools/`)**: Natively queries the **ArXiv API** and **OpenAlex API** (250+ million open-access academic works) without API tokens.
* 🐍 **Automated Code Execution & Data Simulation (`code_interpreter.py`)**: The Methodologist agent dynamically writes vectorized Python scripts (`NumPy`, `Pandas`, `Matplotlib`), runs them in a local sandbox, and renders comparative graphs (`simulation_chart.png`).
* ⚡ **Built-In Simulation Mode**: Allows users to test and visualize the complete multi-agent workflow immediately without waiting for local LLMs to download!

---

## 🚀 How to Share & Use Anywhere on Windows

### Option 1: Use the Portable Bundle (Easiest & Shareable)
We have packaged the entire software into **`Autonomous_Research_Agent_Portable.zip`** (located in your workspace folder).
1. Copy or send `Autonomous_Research_Agent_Portable.zip` to any Windows computer or USB drive.
2. Right-click and select **Extract All...**
3. Open the extracted folder and double-click **`Start_Research_Agent.bat`**.
4. The script will set up the Python environment and launch the sleek Apple Dark OS desktop window automatically!

### Option 2: Rebuilding the Zip Archive
If you modify any source code or add custom personas and want to generate an updated shareable zip file, simply run:
```powershell
python create_portable_bundle.py
```

---

## 🤖 The Multi-Agent Team (CrewAI Role-Based Design)

The system divides complex academic research into four specialized agent personas defined in `config/agents.yaml`:

| Agent Role | Persona Title | Primary Responsibility |
| :--- | :--- | :--- |
| 🕵️ **Literature Scout** | Senior Bibliometric Analyst | Navigates ArXiv and OpenAlex, extracts relevant papers, records citation counts, and synthesizes methodological paradigms and empirical consensus. |
| 🧠 **Gap Analyst** | Chief Theoretical Strategy Analyst | Evaluates literature to uncover scientific contradictions, scalability limits, and unanswered questions. Formulates formalized Pydantic research gaps and testable hypotheses. |
| 🧪 **Methodologist** | Lead Computational Engineer | Designs study methodologies. For computational investigations, writes vectorized Python simulation scripts, executes them in our sandbox tool, and captures empirical metrics and charts. |
| ✍️ **Academic Author** | Distinguished Publication Editor | Assembles all accumulated research artifacts into a formal, structured academic manuscript in clean **Markdown (`.md`)** complete with Abstract, Intro, Methodology, Results tables, Discussion, and References. |

---

## 🔄 The Autonomous Research Workflow

```
[User Inputs Topic in Minimalist Apple Dark Search Bar]
                         │
                         ▼
  ┌──────────────────────────────────────────────┐
  │ 🕵️ Stage 1: Literature Scout                │ ──► Queries ArXiv & OpenAlex APIs
  └──────────────────────┬───────────────────────┘     Extracts Abstracts & Synthesizes Review
                         │
                         ▼
  ┌──────────────────────────────────────────────┐
  │ 🧠 Stage 2: Research Gap Analyst             │ ──► Identifies Scientific Contradictions
  └──────────────────────┬───────────────────────┘     Formulates Research Question & Hypothesis
                         │
                         ▼
  ┌──────────────────────────────────────────────┐
  │ 🧪 Stage 3: Lead Methodologist               │ ──► Writes & Executes Python Simulation Code
  └──────────────────────┬───────────────────────┘     Generates Empirical Metrics & Chart (.png)
                         │
                         ▼
  ┌──────────────────────────────────────────────┐
  │ ✍️ Stage 4: Academic Author & Editor         │ ──► Synthesizes Complete Academic Paper
  └──────────────────────┬───────────────────────┘     Outputs Formal Markdown Manuscript (.md)
                         │
                         ▼
[Desktop App Displays Results & Instant Download Button]
```

---

## 🦙 Setting Up Local Open-Source Models (Ollama)

To run the agent using live, locally hosted LLMs on your Windows PC:
1. Download Ollama from [https://ollama.com/download/windows](https://ollama.com/download/windows) and install it.
2. Open PowerShell or Windows Terminal and pull a free model:
   ```powershell
   # Recommended for academic reasoning & coding:
   ollama run llama3
   ```
3. In our App OS sidebar:
   * **Uncheck** `"Simulation Mode"`.
   * Select `ollama/llama3` from the dropdown.
   * Verify the API endpoint is `http://localhost:11434`.
   * Type any topic and click **"✨ Start Research"**!
