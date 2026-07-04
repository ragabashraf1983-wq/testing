# 🪟 Windows Setup Guide: Autonomous Academic Research Agent

Welcome! This system is architected to run **100% locally and free on Windows** without requiring any paid API keys (no OpenAI, no Anthropic, no subscriptions). It utilizes **CrewAI role-based agent design**, **free academic APIs (ArXiv & OpenAlex)**, and **local open-source LLMs via Ollama**.

---

## ⚡ Quick Start (One-Click Launch)

If you just want to see the application in action immediately:
1. Double-click the included **`run_windows.bat`** file.
2. The script will automatically create a Python virtual environment, install required packages (`streamlit`, `pandas`, `matplotlib`, `requests`, `pydantic`), and launch the interactive web dashboard in your default browser at **`http://localhost:8501`**.
3. In the Web UI sidebar, ensure the checkbox **"Simulation / Demo Mode (No Local LLM Required)"** is **checked**.
4. Click **"🚀 Launch Research"** to watch the multi-agent team investigate renewable energy grids, generate python computational code, produce empirical charts, and draft a complete Markdown academic paper!

---

## 🦙 Setting Up Local Open-Source Models (Ollama)

To run the agent using live, locally hosted LLMs on your GPU or CPU:

### 1. Download & Install Ollama for Windows
* Visit [https://ollama.com/download/windows](https://ollama.com/download/windows) and download `OllamaSetup.exe`.
* Run the installer. Ollama will start automatically in your Windows system tray.

### 2. Pull Your Preferred Open-Source Model
Open a new Windows Terminal or PowerShell and run one of the following commands to pull a free model:

```powershell
# Option A: Llama 3 (8B Parameter - Excellent general reasoner & coder)
ollama run llama3

# Option B: Mistral (7B Parameter - Fast and academic)
ollama run mistral

# Option C: Qwen 2.5 (7B/14B Parameter - Outstanding math & coding capabilities)
ollama run qwen2.5

# Option D: DeepSeek-R1 (Distilled open reasoning model)
ollama run deepseek-r1:8b
```

Once the model downloads, Ollama will run a local server in the background at `http://localhost:11434`.

### 3. Connect the Web Dashboard to Ollama
1. Run `run_windows.bat` or `streamlit run app.py` in your terminal.
2. In the left sidebar of the web interface:
   * **Uncheck** `"Simulation / Demo Mode (No Local LLM Required)"`.
   * Select your installed model from the dropdown (e.g., `ollama/llama3`).
   * Verify the endpoint URL is set to `http://localhost:11434`.
3. Type any research topic and click **"🚀 Launch Research"**!

---

## 🌐 Supporting Other Local APIs (LM Studio, LocalAI, vLLM)

If you prefer using **LM Studio** on Windows instead of Ollama:
1. Download LM Studio from [https://lmstudio.ai](https://lmstudio.ai).
2. Load any GGUF open-source model (e.g., Llama-3-8B-Instruct, Mistral-7B, Qwen).
3. Start the **Local Server** in LM Studio (default port: `1234`).
4. In our Web UI sidebar:
   * Set the model option to `lm-studio-local`.
   * Change the Local API Endpoint URL to `http://localhost:1234`.
   * Click Launch!

---

## 📂 Understanding Where Your Outputs Are Saved

Whenever the agent finishes a research cycle:
* **Academic Manuscript (.md)**: Available for instant visual review and download directly from Tab 5 in the web UI. You can also find pre-saved samples in the `/sample_outputs/` folder.
* **Simulation Charts (.png)**: Whenever the Methodologist agent writes and executes Python code using matplotlib, the output graph is saved as `simulation_chart.png` in the project root and rendered live inside Tab 4 of the dashboard.
