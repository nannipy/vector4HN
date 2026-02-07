# Vector - Hacker News Assistant

Vector is a terminal-based tool that allows you to browse Hacker News, analyze articles and discussions using local LLMs (via Ollama) or cloud-based LLMs (via Google Gemini), and engage in deep-dive chats about the content.

## 🚀 Features

### Multi-Provider Support
-   **Ollama (Local):** Run models like `qwen2.5-coder:32b` or `llama3` locally for privacy and offline use.
-   **Google Gemini (Cloud):** Use high-performance cloud models like `gemini-3-flash-preview` for faster or more complex analysis.
-   **Dynamic Switching:** Easily toggle between providers and models within the application.

### Core Functionality
-   **Live Feed:** Fetches top 50 stories from Hacker News with pagination support.
-   **Automated Analysis:** Extracts article content and summarizes the top 100 comments using BFS (Breadth-First Search) traversal.
-   **Smart Caching:** Saves generated reports and context locally (`reports/`) to prevent redundant API calls and re-analysis.
-   **Usage Logging:** Tracks token usage, duration, and operation types in `logs/stats/usage_stats.csv`.

### AI-Powered Insights
-   **Structured Reports:** Generates comprehensive markdown reports covering:
    -   3-sentence summary.
    -   Pros & Cons / Key Arguments.
    -   Community Sentiment & Controversy.
    -   Hooks.
-   **Contextual Chat:** Engage in a deep-dive conversation about the article. The AI has access to the *full article text* and *nested comment hierarchy*.
-   **Knowledge Library:** Quick access to all previously summarized articles with a dedicated split-view for comparisons.

### TUI (Terminal User Interface)
-   **Interactive Dashboard:** Navigate stories with keyboard controls.
-   **Split-View Report:** View the analysis report and chat window side-by-side.
-   **Settings Screen:** Modify LLM provider, model, and API keys on the fly.
-   **Article Reader:** View the full extracted article text in a dedicated screen.
-   **Library Screen:** Browse and manage previously saved articles.
-   **Select Mode:** Toggle a raw text view to easily select and copy chat content.
-   **Clipboard Integration:** Built-in commands to copy the last answer or the entire chat history.

## ⌨️ Shortcuts

| Context | Key | Action |
| :--- | :--- | :--- |
| **Global** | `Q` | Quit Application |
| **Dashboard** | `↑` / `↓` | Navigate Stories |
| | `Enter` | Analyze Selected Story |
| | `R` | Refresh Feed |
| | `L` | Open Article Library |
| | `N` / `P` | Next / Previous Page |
| | `S` | Open LLM Settings |
| **Report** | `Esc` | Back to Dashboard |
| | `O` | View Original Article Text |
| | `Ctrl+S` | Toggle Select/Copy Mode |
| | `Ctrl+C` | Copy Last Answer |
| | `Ctrl+A` | Copy Full Chat History |
| **Library** | `Esc` | Back to Dashboard |
| | `Enter` | View Article Details |
| | `R` | Refresh Library |
| **Lib Detail**| `Esc` | Back to Library |
| | `C` | Open Chat & Analysis Screen |

## 🛠️ Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd hnscratch
    ```

2.  **Set up a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Includes `httpx`, `beautifulsoup4`, `textual`, `ollama`, `google-genai`, `python-dotenv`, `pytest`, `pytest-asyncio`)*

4.  **LLM Configuration:** 

    **Option A: Ollama (Default)**
    -   Install [Ollama](https://ollama.ai/) and ensure it's running.
    -   Pull a model: `ollama pull llama3`.

    **Option B: Google Gemini**
    -   Get an API key from [Google AI Studio](https://aistudio.google.com/).

5.  **Environment Variables:**
    Create a `.env` file (or copy `.env.example`):
    
    ```env
    LLM_PROVIDER=ollama   # or 'gemini'
    OLLAMA_MODEL=llama3
    OLLAMA_HOST=http://localhost:11434
    GEMINI_API_KEY=your_api_key_here
    GEMINI_MODEL=gemini-3-flash-preview
    ```

## 📖 Usage

To use the `vector` command, first install the project in editable mode:

```bash
./venv/bin/pip install -e .
```

Then you can run the application directly:

```bash
./venv/bin/vector run
```

Settings can be changed at runtime by pressing `S` on the dashboard.

### 🌍 Global Access

To run `vector` from any directory, you can add an alias to your shell profile (e.g., `~/.zshrc` or `~/.bash_profile`):

```bash
alias vector='/Users/giovannibattistapernazza/Documents/Giovanni/Progetti/hnscratch/venv/bin/vector'
```

After adding the alias and restarting your terminal, you can simply run:

```bash
vector run
```

Vector automatically tracks its operations:
-   **App Logs:** General application events are logged to `logs/app/app.log`.
-   **Usage Stats:** Token counts and response times are saved to `logs/stats/usage_stats.csv`.

## 🧪 Testing

Run the test suite to verify the Hacker News client, caching, and logging:

```bash
./venv/bin/pytest tests/
```

Individual test files:
- `tests/test_hn.py`: HN API and scraping.
- `tests/test_caching_logic.py`: Verification of the caching system.
- `tests/test_logging.py`: Verification of the logging and stats system.

## 📁 Project Structure

-   `main.py`: Entry point and configuration loader.
-   `src/hn.py`: Hacker News API client and web scraper.
-   `src/analyze.py`: AI analysis logic (Ollama/Gemini).
-   `src/tui.py`: Textual User Interface screens and logic.
-   `src/logger.py`: Logging and usage statistics utilities.
-   `docs/architecture.md`: Detailed system architecture documentation.
-   `tests/`: Unit tests for core functionality.
-   `reports/`: Cached reports and analysis context.
-   `logs/`: Application logs and usage statistics.

## 📝 License

MIT
